#
# network.py - Network related classes for connecting with the C++ application part
#
# (C) 2019 Carl Zeiss GOM Metrology GmbH
#
# Use of this source code and binary forms of it, without modification, is permitted provided that
# the following conditions are met:
#
# 1. Redistribution of this source code or binary forms of this with or without any modifications is
#    not allowed without specific prior written permission by GOM.
#
# As this source code is provided as glue logic for connecting the Python interpreter to the commands of
# the GOM software any modification to this sources will not make sense and would affect a suitable functioning
# and therefore shall be avoided, so consequently the redistribution of this source with or without any
# modification in source or binary form is not permitted as it would lead to malfunctions of GOM Software.
#
# 2. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or
#    promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import inspect
import pickle
import threading
import traceback
import uuid
import websocket

import gom.__config__
import gom.__encoding__
import gom.__state__
import gom.__tools__

from gom.__common__ import Request


class EncoderContext:
    '''
    \brief Encoding context caring for shared memory segments
    '''

    def __init__(self):
        self.handles = []

    def add(self, handle):
        self.handles.append(handle)

    def __enter__(self):
        self.handles = []
        return self

    def __exit__(self, exception, value, traceback):
        for handle in self.handles:
            handle.close()

        self.handles = []


class DecoderContext:
    '''
    \brief Decoding context caring for shared memory segments
    '''

    def __init__(self):
        self.keys = []

    def add(self, key):
        self.keys.append(key)

    def __enter__(self):
        self.keys = []
        return self

    def __exit__(self, exception, value, traceback):
        if self.keys:
            gom.__common__.__connection__.request(Request.RELEASE, {'keys': self.keys})
        self.keys = []


class Connection:
    '''
    Connection handling class.

    This class opens and maintains a connection to a running ZEISS Inspect software
    instance and implements the API communication protocol.
    '''

    class Attribute:
        TYPE = 'type'
        ID = 'id'
        INTERPRETER = 'interpreter'
        VALUE = 'value'
        STATE = 'state'
        PARAMS = 'params'
        ARGS = 'args'
        KWARGS = 'kwargs'
        ERROR = 'error'
        DESCRIPTION = 'description'
        CODE = 'code'
        LOG = 'log'
        APIKEY = 'apikey'

        class Type:
            ERROR = 'error'
            REQUEST = 'request'
            REPLY = 'reply'
            CALL = 'call'
            RESULT = 'result'
            WAIT = 'wait'

    class Request:
        CALL = 'call'

    class Error:
        ABORT = 'Tom::GScript::BreakException'
        ATTRIBUTE = 'Tom::GScript::AttributeException'
        IMPORT = 'Tom::GScript::ImportException'
        INDEX = 'Tom::GScript::IndexException'
        PYTHON = 'Tom::GScript::PythonException'

    def __init__(self, uri):
        '''
        Initialize connection

        @param uri URI of the remote websocket
        '''
        self._ws = None
        self._thread_id = threading.get_ident()
        self._encoder = gom.__encoding__.CdcEncoder()
        gom.__api__.__cdc_encoder__ = self._encoder
        self._replies = {}
        self._ws = websocket.WebSocket()
        self._ws.connect(uri)

    def send(self, message, context):
        '''
        Send a message to the server
        '''
        message[Connection.Attribute.INTERPRETER] = gom.__config__.interpreter_id
        self._ws.send_bytes(self._encoder.encode(message, context))

    def request(self, command, params):
        '''
        Send request and wait for incoming replies or calls

        This function sends a request to the server and waits until a new message comes in. 
        That message can either be the reply to the request sent or a new  client site function 
        call. The function does not return before the request has been answered.
        '''
        if not isinstance(command, Request):
            raise RuntimeError('Command must be a valid request id')
        if not isinstance(params, dict):
            raise RuntimeError('Command parameters must be a dictionary')
        if threading.get_ident() != self._thread_id:
            raise RuntimeError('Using GOM API features from within different threads is no allowed.')

        with EncoderContext() as context:

            request_id = str(uuid.uuid4())
            self.send({Connection.Attribute.TYPE: Connection.Attribute.Type.REQUEST,
                       Connection.Attribute.APIKEY: gom.__config__.api_access_key,
                       Connection.Attribute.ID: request_id,
                       Connection.Attribute.VALUE: command.value,
                       Connection.Attribute.PARAMS: params}, context)

            #
            # Although the protocol itself is synchroneous, this function is reentrant. So the
            # 'send ()'/'recv ()' calls might be intervowen. So the call to 'recv ()' does not
            # necessarily need to return the result for the previous 'send ()', but for some other
            # action instead.
            #
            # The 'self._replies' dictionary is filled with the received replies which will be
            # consumed by the matching instances then one by one. Each entry contains of a pair
            # (reply type, reply). The 'reply' format depends on that specific type.
            #
            while not request_id in self._replies:

                received = self._ws.recv()

                with DecoderContext() as context:
                    reply = self._encoder.decode(received, context)

                message_type = reply[Connection.Attribute.TYPE]
                message_id = reply[Connection.Attribute.ID]

                #
                # Type 'ERROR': Request failed. Error code/error_log are returned.
                #
                if message_type == Connection.Attribute.Type.ERROR:
                    self._replies[message_id] = (
                        message_type, (reply[Connection.Attribute.ERROR], reply[Connection.Attribute.DESCRIPTION],
                                       reply[Connection.Attribute.CODE], reply[Connection.Attribute.LOG],
                                       reply[Connection.Attribute.VALUE]))

                #
                # Type 'REPLY': Successful request. The request result is returned.
                #
                elif message_type == Connection.Attribute.Type.REPLY:
                    self._replies[message_id] = (message_type, reply[Connection.Attribute.VALUE])

                #
                # Type 'WAIT': No result, call is stalled. This mode is used to implement the service API.
                #              The call to 'gom.run_api (...)' will lead to a 'WAIT' type.
                #
                elif message_type == Connection.Attribute.Type.WAIT:
                    pass

                #
                # Type 'CALL': Request is still active, but an intermediate call to some python function has been
                #              received. This mechanism is used for user defined dialog handlers and service API functions.
                #
                elif message_type == Connection.Attribute.Type.CALL:

                    func = reply[Connection.Attribute.VALUE]
                    args = reply[Connection.Attribute.ARGS]
                    kwargs = reply[Connection.Attribute.KWARGS]

                    try:
                        #
                        # While a client site call is active, exceptions must not be passed via
                        # requests but as a result of that call. Otherwise stack unrolling and
                        # message passing will not work.
                        #
                        gom.__state__.call_function_active += 1

                        result = func(*args, **kwargs)

                        self.send({Connection.Attribute.TYPE: Connection.Attribute.Type.RESULT,
                                   Connection.Attribute.ID: message_id,
                                   Connection.Attribute.STATE: True,
                                   Connection.Attribute.VALUE: result
                                   }, context)

                    except BaseException as e:
                        gom.log.error(traceback.format_exc())

                        e_type, e_value, e_tb = e.__class__, e, e.__traceback__
                        e_tb = gom.__tools__.filter_exception_traceback(e_tb)
                        e_text = f'{str(e_value)}\n\nTraceback (most recent call last):\n{e_tb}'

                        #
                        # If the exception is a GOM break exception, the type must be set to the
                        # GOM break exception type. The API design does not support forwarding
                        # the error code / error message tuple as used in the framework, so a bit
                        # of text comparison is needed here.
                        #
                        e_name = type(e).__name__
                        if str(e_value).startswith("GAPP-0011"):
                            e_name = gom.BreakError.__module__ + '.' + gom.BreakError.__name__

                        self.send({Connection.Attribute.TYPE: Connection.Attribute.Type.RESULT,
                                   Connection.Attribute.ID: message_id,
                                   Connection.Attribute.STATE: False,
                                   Connection.Attribute.VALUE: [
                                       e_name, traceback.format_exc(), pickle.dumps((e_type, e_text))]
                                   }, context)
                    finally:
                        gom.__state__.call_function_active -= 1

                else:
                    raise RuntimeError('Illegal reply format: {reply}')

            if not request_id in self._replies:
                raise RuntimeError('Transmission protocol broken')

            result_type, result = self._replies[request_id]
            del self._replies[request_id]

            if result_type == Connection.Attribute.Type.ERROR:
                error_type, error_description, error_code, error_log, error_data = result
                if error_type == Connection.Error.ABORT:
                    raise gom.BreakError()
                elif error_type == Connection.Error.ATTRIBUTE:
                    raise AttributeError(error_log)
                elif error_type == Connection.Error.IMPORT:
                    raise ImportError(error_log)
                elif error_type == Connection.Error.INDEX:
                    raise IndexError(error_log)
                elif error_type == Connection.Error.PYTHON:
                    e_type, e_value = pickle.loads(error_data)
                    #
                    # gom.RequestError has a different signature compared to Python built-in error, thus we need to process it separately.
                    #
                    if e_type == gom.RequestError:
                        raise gom.RequestError(error_description, error_code, e_value)
                    raise e_type(f'{e_value}\nCalled from here:')
                else:
                    raise gom.RequestError(description=error_description, error_code=error_code, error_log=error_log)

        return result
