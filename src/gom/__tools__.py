#
# tools.py - Tool classes and functions
#
# This is the wrapper script which is started together with the Python interpreter instance
# when an application script is executed. It prepares the interpreter to communicate with
# the application instances and cares for initializing the gom specific data types.
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

import importlib.abc
import importlib.machinery
import collections.abc
import logging
import os
import sys
import traceback

import gom.__common__
from gom.__common__ import Constants, Request


def set_result(value):
    return gom.__common__.__connection__.request(Request.RESULT, {'result': value})


def wrap_code_as_function(code):
    '''
    Wrap a piece of code into a function body so that a 'return <result>' can be issued
    '''

    lines = ['\t' + line for line in code.split('\n')]

    code = 'def {name} ():\n{code}\n'.format(name=Constants.wrapped_function_name, code='\n'.join(lines))
    code += '{var} = {name} ()\n'.format(var=Constants.wrapped_result_var_name, name=Constants.wrapped_function_name)

    return code


def filter_exception_traceback(tb):
    '''
    Remove system and glue logic frames from an exception traceback
    '''
    system_frame_prefix = os.path.dirname(os.path.realpath(__file__))
    executed_file_prefix = os.path.split(system_frame_prefix)[0] + '\\'

    #
    # Traceback frames originating from the 'gom' system module are completely skipped.
    # The temporary directory information is removed from the traceback file paths.
    #
    filtered = []
    for frame, line in traceback.walk_tb(tb):
        if not gom.__config__.strip_tracebacks:
            filtered.append((frame, line))
        elif not os.path.realpath(frame.f_code.co_filename).startswith(system_frame_prefix):
            if not '\\importlib\\' in frame.f_code.co_filename:
                if not 'frozen importlib' in frame.f_code.co_filename:
                    if str(frame.f_code.co_filename) != executed_file_prefix + '__gom_run_script__.py':
                        filtered.append((frame, line))

    return ''.join(traceback.StackSummary.extract(
        filtered).format()).replace(executed_file_prefix, '')


class StdoutFlusher:
    '''
    \brief This class writes stdout events and flushes the text buffer immediately
    '''

    def __init__(self):
        self.stdout = None
        self.closed = False

    def write(self, text):
        self.stdout.write(text)
        self.stdout.flush()

    def flush(self):
        self.stdout.flush()

    def close(self):
        pass

    def __enter__(self):
        self.stdout = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, ext_type, exc_value, traceback):
        sys.stdout = self.stdout


class StderrFlusher:
    '''
    \brief This class writes stderr events and flushes the text buffer immediately
    '''

    def __init__(self):
        self.stderr = None
        self.closed = False

    def write(self, text):
        self.stderr.write(text)
        self.stderr.flush()

    def flush(self):
        self.stderr.flush()

    def close(self):
        pass

    def __enter__(self):
        self.stderr = sys.stderr
        sys.stderr = self
        return self

    def __exit__(self, ext_type, exc_value, traceback):
        sys.stderr = self.stderr


class ImportHookChainedLoader:
    '''
    Wrapping import loader
    '''

    def __init__(self, loader, callback):
        self._loader = loader
        self._callback = callback

    def load_module(self, fullname):

        module = self._loader.load_module(fullname)

        self._callback(module)

        return module


class ImportHookFinder:
    '''
    Finder class for importing modules with calling a hook function afterwards
    '''

    def __init__(self):
        self._hooks = {}
        self._active = False

    def register_hook(self, name, callback):
        '''
        Register hook which is called upon loading of a module
        '''
        self._hooks[name] = callback

        # If the module is already loaded, the hook is executed immadiately
        if name in sys.modules:
            callback(sys.modules[name])

    def find_module(self, fullname, path=None):

        if not self._active and fullname in self._hooks:
            self._active = True
            loader = importlib.find_loader(fullname, path)
            self._active = False

            if loader:
                return ImportHookChainedLoader(loader, self._hooks[fullname])

        return None


class ResourceImportLoader (importlib.abc.SourceLoader):
    '''
    Loader class for resource based modules and packages
    '''

    def __init__(self, code, path):
        self.code = code
        self.path = path

    def get_data(self, path):
        return self.code

    def get_filename(self, fullname):
        return self.path

    def get_source(self, fullname):
        return self.code


class ResourceImportFinder (importlib.abc.MetaPathFinder):
    '''
    Finder class for resource based modules and packages

    This object is registered in the 'sys.metapath' list and will be called if
    any 'import' statement is executed and the package/code to be imported must
    be located.

    @param fullname Full (qualified) name of the object to be imported
    @param path     Value of the '__path__' variable from the parent package for relative imports
    @return Module spec or 'None' if the module was not found
    '''

    def find_spec(self, fullname, path, target=None):

        if gom.__common__.__connection__ == None:
            return None

        #
        # The application can return the code to be imported
        #
        params = gom.__common__.__connection__.request(Request.IMPORT, {'name': fullname, 'path': str(path)})
        if params is None:
            return None

        spec = importlib.machinery.ModuleSpec(
            name=fullname,
            loader=ResourceImportLoader(params['code'], params['name']),
            origin=params['name'],
            loader_state=None,
            is_package=params['is_package']
        )

        spec.cached = False
        spec.has_location = True

        return spec


class EnvironmentListener (collections.abc.Mapping):
    '''
    \brief Listener for changes to the environment variables
    '''

    def __enter__(self):
        self.environ = os.environ
        self.putenv = os.putenv

        os.environ = self
        os.putenv = self

    def __exit__(self, ext_type, exc_value, traceback):
        os.putenv = self.putenv
        os.environ = self.environ

    def get(self, key, default=None):
        return self.environ.get(key, default)

    def items(self):
        return self.environ.items()

    def keys(self):
        return self.environ.keys()

    def values(self):
        return self.environ.values()

    def pop(self, key, default=None):
        return self.environ.pop(key, default)

    def popitem(self):
        return self.environ.popitem()

    def setdefault(self, key, value):
        self.environ.setdefault(key, value)

    def update(self, other):
        return self.environ.update(other)

    def copy(self):
        return self.environ.copy()

    def __contains__(self, key):
        return self.environ.__contains__(key)

    def __getitem__(self, key):
        return self.environ.__getitem__(key)

    def __delitem__(self, key):
        self.environ.__delitem__(key)
        if gom.__common__.__connection__:
            gom.__common__.__connection__.request(Request.SETENV, {'name': key, 'value': None})

    def __setitem__(self, key, value):
        self.environ.__setitem__(key, value)
        if gom.__common__.__connection__:
            gom.__common__.__connection__.request(Request.SETENV, {'name': key, 'value': str(value)})

    def __call__(self, key, value):
        self.putenv(key, value)

        if gom.__common__.__connection__:
            if type(key) == bytes:
                key = key.decode(sys.getfilesystemencoding())
            if type(value) == bytes:
                value = value.decode(sys.getfilesystemencoding())

            gom.__common__.__connection__.request(Request.SETENV, {'name': key, 'value': value})

    def __iter__(self):
        return self.environ.__iter__()

    def __len__(self):
        return self.environ.__len__()

    def __repr__(self):
        return self.environ.__repr__()

    def __str__(self):
        return self.environ.__str__()


class ExitHandler:
    '''
    \brief This class wraps the standard 'sys.exit ()' functions
    '''

    original_exit = None

    def __enter__(self):
        ExitHandler.original_exit = sys.exit
        sys.exit = ExitHandler.exit
        return self

    def __exit__(self, ext_type, exc_value, traceback):
        sys.exit = ExitHandler.original_exit

    @staticmethod
    def exit(exitcode):
        gom.__common__.__connection__.request(Request.EXIT, {'code': exitcode})
        ExitHandler.original_exit(exitcode)


class LogHandler (logging.Handler):
    '''
    Handler for logging messages

    Forwards the log messages to the application for server side log message handling
    '''

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')

    def emit(self, record):
        try:
            gom.__common__.__connection__.request(Request.LOG, {'message': self.format(record)})
        except Exception as e:
            self.handleError(record)


class Console:
    '''
    \brief Unfiltered stream for direct console output (for test script purposes)
    '''

    def write(self, text):
        gom.__common__.__connection__.request(Request.CONSOLE, {'message': text})

    def flush(self):
        pass


class NumpyErrorMessageFacade:
    '''
    \brief Numpy error message facade

    This class is used to raise a self speaking error message in case of using
    numpy functions without prior importing the numpy library. This is needed because
    the token insertion dialog will encapsulate token access with 'np.array ()' which
    leads to an error message if there is no 'import numpy as np' in the script.
    '''

    def __getattr__(self, key):
        raise AttributeError('Numpy module is not installed or imported.'
                             ' To use this feature, you have to add "import numpy as np" to your script after installing the numpy python package.'
                             '\n\nPlease refer to the GOM knowledge base for details.')


def __excepthook__(exc_type, exc_value, tb):
    '''
    Exception handler function

    This handler function is called whenever an exception makes its way through the whole
    stack unexcepted excluding 'SystemExit'.
    '''

    #
    # A 'BreakError' will just terminate the script without any further error handling
    #
    if exc_type == gom.BreakError:
        gom.__exit_handler__.__exit__(exc_type, exc_value, tb)
        sys.exit(0)

    if gom.__state__.call_function_active == 0:
        tb = filter_exception_traceback(tb)

        gom.__common__.__connection__.request(Request.EXCEPTION, {
            'name': str(exc_type.__name__),
            'text': str(exc_value),
            'traceback': tb
        })

        gom.log.error(f'{exc_type.__name__}: {exc_value}\n{tb}')

    print(f'{exc_type.__name__}: {exc_value}', file=sys.stderr)
    print(tb, file=sys.stderr)

    #
    # The exit handler triggers application exits if '-exitonscriptexit' is set. This is meant to be
    # explicitly initiated from within scripts, not in error cases. So the exit handler must be shutdown
    # here before the silent script exit.
    #
    gom.__exit_handler__.__exit__(exc_type, exc_value, tb)
    sys.exit(1)
