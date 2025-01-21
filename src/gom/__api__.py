#
# api.py - gom.api infrastructure access classes
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

import importlib
import importlib.util
import inspect
import json
import re
import warnings

import gom
import gom.__common__
from gom.__common__ import Contribution, Request


__encoder__ = None
__cdc_encoder__ = None


class GomApiRegistry:
    '''
    Registry for API functions

    Python functions which are decorated with the '@apifunction' decorator will be registered in this
    registry. The registry is then used to forward the available function set to the C++ side of the
    application.
    '''

    def __init__(self):
        self._functions = []
        self._contributions = []
        self._services = []

    def register_function(self, func):
        '''
        Register API function. The set of functions collected here is sent to the application later and will
        lead to correct service registration.
        '''
        self._functions.append(func)

    def register_contribution(self, contribution):
        '''
        Register API contribution
        '''
        if not issubclass(contribution, Contribution):
            raise RuntimeError(
                f'Class {contribution} registered as a contribution must be derived from gom.__common__.Contribution')

        self._contributions.append(contribution())

    def register_service(self, service):
        '''
        Register service namespace. Each service fill be listed here.

        This function is basically needed as a workaround for missing EDM capabilties. The EDM and especially the
        EDM-GOM-API does not have efficient value conversion yet. There is always some JSON/CDC/BSON conversion involved
        and the data types do not match. Therefor, the registered service will use a direct script-to-script connection
        for performance reasons. The API parts which are affected by that are registered here.

        @param service Name of the service to register (without 'gom.api.' prefix)
        '''
        self._services.append(service + '.')

    def is_service(self, module):
        '''
        Return if the given module is a registered service

        @param module Module name
        @return 'True' if the given module is a registered script based service and the script-to-script short link can be used.
        '''
        return (module + '.') in self._services

    def get_declaration(self):
        '''
        Get the declaration of all registered functions

        This function returns the declarations of all registered API functions. It is passed to the C++ 
        application to make the functions available for the script engine.

        @return List of dictionaries containing the module name, function name and the argument list
        '''

        declaration = []

        for func in self._functions:

            #
            # The 'args' field is used to generate the API function call. If there
            # were variable positional or keywords passed (*args, **kwargs), these have
            # to be passed through.
            #
            args = []
            for name, value in inspect.signature(func).parameters.items():
                if value.kind == value.VAR_POSITIONAL:
                    name = '*' + name
                elif value.kind == value.VAR_KEYWORD:
                    name = '**' + name
                args.append(name)

            #
            # The function signature must be adapted to avoid exposing the numpy array wrappers
            #
            signature = str(inspect.signature(func))
            signature = re.sub(r"<function Array\.numpy_array_wrapper at 0x[0-9A-Fa-f]+>", "np.array", signature)
            signature = re.sub(r"gom\.Array\.numpy_array_wrapper", "np.array", signature)

            declaration.append({
                'name': func.__name__,
                'callable': func,
                'args': args,
                'signature': signature,
                'doc': inspect.getdoc(func),
                'comment': inspect.getcomments(func)
            })

        return declaration


__api_registry__ = GomApiRegistry()


class GomApiError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class GomApiMethod(object):
    '''
    Class representing an API method bound to an object instance
    '''

    def __init__(self, instance, id, name):
        '''
        Constructor

        @param instance Object instance this method is bound to. 
        @param id       Object id to identify the related object in the application
        @param name     Name of the method to call
        '''
        self.__instance = instance  # Backlink to prevent the instance from getting garbage collected
        self.__id = id
        self.__name = name

    def __call__(self, *args):
        return __encoder__.call_method(self.__id, self.__name, args)


class GomApiInstance(object):
    '''
    Class representing an object instance

    Every generic object representation in python has an id which references the C++ counterpart.
    The C++ object is valid and accessible via that id during the interpreter livetime if not
    deleted explicitly via a 'release' API call.
    '''

    def __init__(self, id):
        self.__id = id

    def __del__(self):
        try:
            __encoder__.call_function('internal', 'release', [self.__id])
        except:
            pass

    def __getattr__(self, method):
        return GomApiMethod(self, self.__id, method)

    def __api_json__(self):
        return {
            '$type': 'instance',
            'id': self.__id
        }


class GomApiModuleOrFunction(object):
    '''
    Class representing either a module or a function

    It cannot be distinguished between these two types until a call operation is executed. So
    'gom.api.tools.initialize' can either be a part of a longer path or already the function to
    be called as a leaf in the object tree.
    '''

    def __init__(self, path, function):
        '''
        Constructor

        @param path Path representing the first [0:-1] parts of the whole path expression
        @param function Function name representing the last part of the whole path expression 
        '''
        self.__path = path
        self.__function = function

    def __getattr__(self, member):
        return GomApiModuleOrFunction(self.__path__(), member)

    def __call__(self, *args, **kwargs):
        return __encoder__.call_function('.'.join(self.__path), self.__function, args, kwargs)

    def __repr__(self):
        return '.'.join(['gom', 'api'] + self.__path__())

    def __path__(self):
        return self.__path + [self.__function] if self.__function else self.__path


class GomApiRoot(object):
    '''
    API root node

    Top level node of an API sub path like 'gom.api.addons'. Must be a child of the global 
    'gom.api' object.
    '''

    def __init__(self, name):
        self.name = name

    def __getattr__(self, module):
        return GomApiModuleOrFunction([self.name], module)


class Encoder(object):
    '''
    Encoder/decoder class for python/C++ communication

    This encoder implements the API call encoding. The API supports basic regular
    types on one hand, and objects instances plus shared memory encoded blocks on
    the other hand. To be able to handle this in general, the API communication protocol
    consists of a CDC blob embedded into a JSON message with some additional administrative
    information.
    '''

    class CustomJSONEncoder(json.JSONEncoder):
        '''
        Custom encoder class to generate the JSON request parameter
        '''

        def __init__(self, *args, **kwargs):
            self.context = kwargs.pop('encoding_context', None)
            super().__init__(*args, **kwargs)

        def default(self, obj):

            #
            # GOMAPI objects can JSON encode themselves and implement a method for that
            #
            if (hasattr(obj, "__api_json__") and obj.__api_json__ is not None):
                return obj.__api_json__()

            #
            # All other types are CDC encoded. This provides a correct shared memory block
            # handling and performance benefits in general. The BSON format used under the
            # hood supports binary transmissions.
            #
            try:
                data = __cdc_encoder__.encode(obj, self.context)
                json = {'type': 'cdc_encoded_object', 'cdc_data': list(data)}
            except Exception as e:
                raise TypeError("Error in CDC encoding" + str(e))

            return json

    class CustomJSONDecoder(json.JSONDecoder):
        '''
        Custom decoder class to generate local objects from the JSON reply
        '''

        def __init__(self, *args, **kwargs):
            self.context = kwargs.pop('decoding_context', None)
            self.decoder_map = {
                'instance': self.__instance_creator__,
                'structure': self.__struct_decoder__,
                'reference': lambda obj: gom.Item(obj['id'], obj['category']),
                'V2': lambda obj: gom.Vec2d(obj['x'], obj['y']),
                'V3': lambda obj: gom.Vec3d(obj['x'], obj['y'], obj['z']),
                'cdc_encoded_object': self.__decode_cdc__
            }

            kwargs["object_hook"] = self.__decode__

            super().__init__(*args, **kwargs)

        def __decode__(self, obj):
            #
            # Regular types are plain JSON decoded and can just be returned
            #
            if not '$type' in obj:
                return obj

            #
            # Special types are decoded by the matching decoder functions
            #
            type_entry = self.decoder_map.get(obj['$type'])
            if type_entry is None:
                return obj

            return type_entry(obj)

        def __decode_cdc__(self, obj):
            '''
            Decode CDC encoded part of the reply
            '''
            return __cdc_encoder__.decode(bytearray(bytes(obj['cdc_data'])), self.context)

        def __struct_decoder__(self, obj):
            result = type(obj['name'], (object,), dict())()
            for key, value in obj['fields'].items():
                result.__setattr__(key, value)
            return result

        def __instance_creator__(self, obj):
            '''
            Function called in the context of JSON object resolution to convert
            a JSON reply into a python side object

            @param obj JSON object to be converted into a python object
            '''

            #
            # There are two variants of python side objects:
            #
            # - 'Real' objects which have an imported module definition and full spec. These
            #   objects are derived from the 'gom.api.Object' type and do have type save definitions
            #   defined in the related C++ files.
            # - 'Generic' objects which are instantiated on-the-fly. This is the old EDM method of
            #   instantiation. These objects are all instances of type 'gom.api.GomApiInstance' and do
            #   not have a fixed type definition.
            #
            if 'typename' in obj and obj['typename']:

                #
                # Try to find a classtype with the specified type name. If found, this class can
                # be instantiated directly.
                #
                typename = 'gom.api.' + obj['typename']
                module_name, class_name = typename.rsplit('.', 1)

                if importlib.util.find_spec(module_name):
                    module = importlib.import_module(module_name)

                    if hasattr(module, class_name):
                        classtype = getattr(module, class_name)

                        if type(classtype) == type and issubclass(classtype, gom.__api__.Object):
                            return classtype(obj['id'])
                        else:
                            warnings.warn(
                                f'The type \'{typename}\' is returned as a generic instance but conflicts with an imported type or namespace. Consider renaming it.')

            #
            # Fallback for generic types
            #
            return GomApiInstance(obj['id'])

    def encode(self, req):
        from gom.__network__ import EncoderContext, DecoderContext

        with EncoderContext() as context:
            string = json.dumps(req, cls=Encoder.CustomJSONEncoder, encoding_context=context)

        string = gom.__common__.__connection__.request(Request.API, {'json': string})

        with DecoderContext() as context:
            reply = json.loads(string, cls=Encoder.CustomJSONDecoder, decoding_context=context)

        if 'error' in reply:
            raise GomApiError(reply['error'])
        if 'result' in reply:
            return reply['result']
        raise KeyError()

    def call_function(self, module, function, args, kwargs):

        #
        # Script-to-script call shortlink. This way, various value conversions can be skipped and shared memory for
        # large data sets will be available. The regular EDM-API link does not provide that.
        #
        if __api_registry__.is_service(module):
            return gom.__common__.__connection__.request(Request.SERVICE, {'module': module, 'function': function, 'args': args, 'kwargs': kwargs})

        request = {
            'module': module,
            'call': function,
            'params': args
        }

        return self.encode(request)

    def call_method(self, instance, method, args):
        request = {
            'instance': instance,
            'call': method,
            'params': args
        }

        return self.encode(request)


__encoder__ = Encoder()


def __call_function__(*args, **kwargs):
    '''
    Execute API function call

    This function is used by the generated API code to execute calls to global functions.
    '''
    frame = inspect.currentframe().f_back

    module = inspect.getmodule(frame).__name__
    prefix = 'gom.api.'
    if module.startswith(prefix):
        module = module[len(prefix):]

    return __encoder__.call_function(module, frame.f_code.co_name, args, kwargs)


class Object:
    '''
    Base class for all API based objects

    This class is used as a base class for generated API objects 
    '''

    def __init__(self, instance_id):
        self.__instance_id = instance_id

    def __del__(self):
        try:
            __encoder__.call_function('internal', 'release', [self.__instance_id])
        except:
            pass

    def __call_method__(self, name, *args):
        return __encoder__.call_method(self.__instance_id, name, args)

    def __api_json__(self):
        return {
            '$type': 'instance',
            'id': self.__instance_id
        }
