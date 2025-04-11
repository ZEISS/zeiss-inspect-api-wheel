#
# gom.py - Access to the GOM application interface
#
# This module implements the 'gom' layer including access to all elements via 'gom.app',
# executing commands via 'gom.script.command_name' and various special classes for process
# communication. While the 'server.py' module is started to setup and start the script execution,
# the 'gom' module is imported by the executed scripts to represent the data and command
# interface to the application.
#
# (C) 2023 Carl Zeiss GOM Metrology GmbH
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

import atexit
import inspect
import logging
import math
import mmap
import os
import sys
import urllib.parse
import uuid
import warnings

import importlib.util

import gom.__api__
import gom.__config__
import gom.__state__
import gom.__test__
import gom.__tools__

import gom.__common__
from gom.__common__ import Request

import gom.api
import gom.api.addons
import gom.api.introspection
import gom.api.script_resources


def tr(text, id=None):
    '''
    \brief Return translated version of the given test

    This function is added to the global namespace of the executed script and can be used
    to receive translations from the packages *.xlf files.

    Being a global function, this function will be available in the executed script, too.

    \param text Text to be translated
    \param id   Translation id of the text. Optional, used in the GOM internal translation process.
    \return Translation in the current locale
    '''
    translated = text

    try:
        translated = gom.__common__.__connection__.request(Request.TRANSLATE, {
            'text': text, 'id': id if id else ''})['translation']
    except:
        pass

    return translated


class RequestError (RuntimeError):
    '''
    \brief Exception type raised from an failed request
    '''

    def __init__(self, description, error_code, error_log):

        super().__init__(error_code, error_log)

        self.description = description
        self.error_code = error_code
        self.error_log = error_log

    def __str__(self):
        if not self.error_log.startswith(self.description):
            return '{code}: {description}\n\n{log}'.format(code=self.error_code, description=self.description, log=self.error_log)
        else:
            return '{code}: {log}'.format(code=self.error_code, log=self.error_log)

    # For compatibility reasons
    def __getitem__(self, key):
        if key == 0:
            return self.error_code
        elif key == 1:
            return self.error_log

        raise RuntimeError('Invalid index')

    def __repr__(self):
        return 'RequestError: code={code}, description={description}, log={log}'.format(code=self.error_code, description=self.description, log=self.error_log)

    # enable pickle support
    def __reduce__(self):
        return (self.__class__, (self.description, self.error_code, self.error_log))


class BreakError (Exception):
    '''
    \brief Exception raised if the running script is to be terminated
    '''

    def __init__(self, text=''):
        super().__init__(text)

    def __repr__(self):
        return 'BreakError'


class Indexable (object):
    '''
    \brief Object representing a indexable proxy to some partially resolved item.

    Example: 'gom.app.project.inspection['Point cloud'].coordinate' does not provide
    a token itself. Instead, it can be used together with an index to access single
    point coordinates of the point cloud. So an gom.Indexable object is constructed in
    this case to be a placeholder for point accessed in the Python domain.
    '''

    def __init__(self, item, token, size):
        self.item = item
        self.token = token
        self.size = size

    def __eq__(self, other):
        return isinstance(other, Indexable) and \
            self.item == other.item and \
            self.token == other.token and \
            self.size == other.size

    def __getitem__(self, key):
        return gom.__common__.__connection__.request(Request.INDEX,
                                                     {'item': self.item, 'name': self.token, 'index': key})

    def __getattribute__(self, key):
        if key == '__doc__':
            return gom.__common__.__connection__.request(Request.DOC,
                                                         {'object': self})
        return object.__getattribute__(self, key)

    def __iter__(self):
        elements = gom.__common__.__connection__.request(Request.INDEX,
                                                         {'item': self.item, 'name': self.token, 'index': None})
        for e in elements:
            yield e

    def __len__(self):
        return self.size

    def __repr__(self):
        return 'Indexable (item={item}, token={token}, size={size})'.format(item=self.item, token=self.token, size=self.size)

    def __json__(self):
        return {'item': self.item,
                'token': self.token,
                'size': self.size}

    @staticmethod
    def from_params(params):
        return Indexable(item=params['item'],
                         token=params['token'],
                         size=params['size'])


class Item (object):
    '''
    \briefAn object of this class represents a single item in the applications item space

    Each Tom::ScriptObject has a unique item id, like 'I#!1234', which is used to
    link an item to the corresponding C++ object.
    '''

    def __init__(self, id, category=0, stage=-1):
        self.__dict__['__id__'] = id
        self.__dict__['__category__'] = category
        self.__dict__['__stage__'] = stage

    def get(self, key, index=None):
        return gom.__common__.__connection__.request(Request.GET,
                                                     {'item': self, 'name': key, 'index': index})

    def get_tokens(self):
        return gom.__common__.__connection__.request(Request.TOKENS,
                                                     {'item': self})

    def filter(self, expression, condition=None):
        return gom.__common__.__connection__.request(Request.FILTER,
                                                     {'item': self, 'expression': expression, 'condition': condition})

    def __lt__(self, other):
        return gom.__common__.__connection__.request(Request.LESS,
                                                     {'item': self, 'other': other})

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)

    def __gt__(self, other):
        return not self.__eq__(other) and not self.__lt__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __eq__(self, other):

        if isinstance(other, Item) and self.__category__ == other.__category__:
            return self.__id__ == other.__id__

        #
        # If not equal in all relevant parameters, item must be compared on the server side
        # to be able to handle and resolve actual and nominal values references correctly.
        #
        return gom.__common__.__connection__.request(Request.EQUAL,
                                                     {'item': self, 'other': other})

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getattribute__(self, key):
        if key == '__doc__':
            return gom.__common__.__connection__.request(Request.DOC,
                                                         {'object': self})
        return object.__getattribute__(self, key)

    def __getattr__(self, key):
        if key == 'in_stage':
            class StageSelector:
                def __init__(self, category, id):
                    self.id = id
                    self.category = category

                def __getitem__(self, key):
                    return Item(self.id, self.category, key)

            return StageSelector(self.__dict__['__category__'], self.__dict__['__id__'])

        # it can happen that a DataInterface::Package is sent as token result, so we have to release shared memory
        return gom.__common__.__connection__.request(Request.GETATTR,
                                                     {'item': self, 'name': key, 'stage': self.__stage__})

    def __setattr__(self, key, value):
        gom.__common__.__connection__.request(Request.SETATTR,
                                              {'item': self, 'name': key, 'value': value})

    def __getitem__(self, key):
        return gom.__common__.__connection__.request(Request.KEY,
                                                     {'item': self, 'name': key})

    def __len__(self):
        return gom.__common__.__connection__.request(Request.LEN,
                                                     {'item': self})

    def __repr__(self):
        if self.__id__.startswith('gom.'):
            return self.__id__

        return gom.__common__.__connection__.request(Request.REPR,
                                                     {'item': self})

    def __hash__(self):
        return hash(self.__id__)

    def __json__(self):
        return {'id': self.__id__, 'category': self.__category__, 'stage': self.__stage__}

    def __api_json__(self):
        return {'$type': 'reference', 'id': self.__id__, 'category': self.__category__}

    @staticmethod
    def from_params(params):
        return Item(id=params['id'], category=params['category'], stage=params['stage'])


class Array (object):
    '''
    \brief Data array container representation

    An object of this type is being returned if the 'data' token is queried from
    an item, like in 'element.data.coordinate'. So after the 'data' part of the
    expression it is clear that tokens queried from here on should result in
    data packages instead of single values tokens.
    '''

    _numpy_asarray_func = None

    def __init__(self, project, item, key, index, selected, transformation):
        self.project = project
        self.item = item
        self.key = key
        self.index = index
        self.selected = selected
        self.transformation = transformation

    def __eq__(self, other):
        return self.project == other.project and \
            self.item == other.item and \
            self.key == other.key and \
            self.index == other.index and \
            self.selected == other.selected and \
            self.transformation == other.transformation

    def __getattr__(self, key):

        if key.startswith('_'):
            result = super().__getattr__(key)
        elif key == 'shape':
            result = gom.__common__.__connection__.request(Request.DATA_SHAPE,
                                                           {'data': self})
            if isinstance(result, list):
                result = tuple(result)
        else:
            result = gom.__common__.__connection__.request(Request.DATA_ATTR,
                                                           {'data': self,
                                                            'name': key})

        return result

    def __getitem__(self, key):

        if not isinstance(key, int):
            raise TypeError('Index must be an integer type')

        return gom.__common__.__connection__.request(Request.DATA_INDEX,
                                                     {'data': self,
                                                      'key': key})

    def __repr__(self):

        name = repr(self.item)
        name += '.data' if not self.selected else '.selection'
        name += '.' + self.key if len(self.key) > 0 else ''
        name += ''.join(['[{i}]'.format(i=i) for i in self.index])

        shape = gom.__common__.__connection__.request(Request.DATA_SHAPE,
                                                      {'data': self})
        if isinstance(shape, list):
            shape = tuple(shape)

        return 'gom.Array (element={name}, shape={shape})'.format(name=name, shape=shape)

    def __json__(self):
        return {'project': self.project, 'item': self.item, 'key': self.key, 'index': self.index, 'selected': self.selected}

    @staticmethod
    def from_params(params):
        return Array(project=params['project'], item=params['item'], key=params['key'], index=params['index'], selected=params['selected'], transformation=None)

    @staticmethod
    def numpy_array_wrapper(*args, **kwargs):

        global np
        import numpy as np

        if len(args) == 1 and len(kwargs) == 0 and type(args[0]) == Array:
            result = gom.__common__.__connection__.request(Request.DATA_ARRAY,
                                                           {'data': args[0]})

            if isinstance(result, np.ndarray):
                return result

            raise RuntimeError('Numpy compatible array expected, but got {type}'.format(type=type(result)))

        return Array._numpy_array_func(*args, **kwargs)

    @staticmethod
    def numpy_asarray_wrapper(*args, **kwargs):

        global np
        import numpy as np

        if len(args) == 1 and len(kwargs) == 0 and type(args[0]) == Array:

            result = gom.__common__.__connection__.request(Request.DATA_ARRAY,
                                                           {'data': args[0]})

            if isinstance(result, np.ndarray):
                return result

            raise RuntimeError('Numpy compatible array expected, but got {type}'.format(type=type(result)))

        return Array._numpy_asarray_func(*args, **kwargs)

    @staticmethod
    def numpy_imported_hook(module):
        Array._numpy_array_func = module.array
        module.array = Array.numpy_array_wrapper

        Array._numpy_asarray_func = module.asarray
        module.asarray = Array.numpy_asarray_wrapper


class ResourceAccess (object):
    '''
    \brief Resource accessing class

    This object represents the virtual script object 'gom.app.resource' which can
    be used to access script resources. The resource is returned as a 'bytes ()' array.
    '''

    def __init__(self):
        pass

    def __eq__(self, other):
        return True

    def __getitem__(self, key):
        return gom.__common__.__connection__.request(Request.RESOURCE_KEY, {'name': key})

    def __len__(self):
        return gom.__common__.__connection__.request(Request.RESOURCE_LEN, {})

    def __repr__(self):
        return 'Resources ()'

    def __json__(self):
        return {}

    @staticmethod
    def from_params(params):
        return ResourceAccess()


class Command (object):
    '''
    \brief Command or command namespace representing object. 

    This is anything starting with 'gom.script' or 'gom.interactive'
    '''

    valid_overload_objects = []

    def __init__(self, name):
        self.__dict__['__name__'] = name
        self.__dict__['__overrides__'] = {}

    def __eq__(self, other):
        return isinstance(other, Command) and \
            self.__name__ == other.__name__

    def __getattribute__(self, key):
        if key == '__doc__':
            return gom.__common__.__connection__.request(Request.DOC,
                                                         {'object': self})

        return object.__getattribute__(self, key)

    def __getattr__(self, key):
        if key == '__name__':
            return self.__dict__['__name__']
        elif key == '__overrides__':
            return self.__dict__['__overrides__']
        elif key in self.__dict__['__overrides__']:
            return self.__dict__['__overrides__'][key]

        return gom.__common__.__connection__.request(Request.GETATTR,
                                                     {'item': Item(self.__name__), 'name': key})

    def __setattr__(self, key, value):
        '''
        Overload commands for kiosk test scripts. This function is intended for faking a complete GOM
        measuring setup for the kiosk test scripts only.
        '''
        if self.__name__ not in Command.valid_overload_objects:
            raise RuntimeError('Illegal command overload for command group {name}'.format(name=self.__name__))

        self.__overrides__[key] = value

    def __call__(self, *args, **kwargs):

        result, warning = gom.__common__.__connection__.request(Request.COMMAND,
                                                                {'command': self.__name__, 'parameters': kwargs})

        if warning:
            warnings.warn('While executing {command}: {warning}'.format(command=self.__name__, warning=warning))

        return result

    def __repr__(self):
        return self.__name__

    def __json__(self):
        return {'name': self.__name__}

    @staticmethod
    def from_params(params):
        return Command(name=params['name'])

    @staticmethod
    def create_overload_group(name):
        Command.valid_overload_objects.append(name)
        return Command(name)


class Object (object):
    '''
    \brief Value representing a generic object instance without specialized script type interface
    '''

    def __init__(self, params):
        self.__object_type__ = params['type']
        self.__object_repr__ = params['repr']

        for attr in params['attributes']:
            self.__dict__[attr['name']] = attr['value']

    def __eq__(self, other):
        if isinstance(other, Object) and \
                self.__object_type__ == other.__object_type__ and \
                self.__dict__ == other.__dict__:
            return True

        if isinstance(other, str) and other == self.__object_repr__:
            return True

        return False

    def __getattribute__(self, key):
        if key == '__doc__':
            return gom.__common__.__connection__.request(Request.DOC,
                                                         {'object': self.__object_type__})
        return object.__getattribute__(self, key)

    def __repr__(self):
        return self.__object_repr__

    def __str__(self):
        return self.__object_repr__

    @staticmethod
    def from_params(params):
        return Object(params)


class Vec2d:
    '''
    Fast wrapped for the gom.Vec2d object
    '''

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getattribute__(self, key):
        if key == '__doc__':
            return gom.__common__.__connection__.request(Request.DOC,
                                                         {'object': self})
        return object.__getattribute__(self, key)

    def __add__(self, other):
        assert isinstance(other, Vec2d)
        return Vec2d(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        assert isinstance(other, Vec2d)
        return Vec2d(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        assert isinstance(other, Vec2d) or isinstance(other, float) or isinstance(other, int)
        if isinstance(other, Vec2d):
            return self.x * other.x + self.y * other.y

        return Vec2d(self.x * other, self.y * other)

    def __truediv__(self, other):
        assert isinstance(other, float) or isinstance(other, int)
        return Vec2d(self.x / other, self.y / other)

    def __neg__(self):
        return Vec2d(-self.x, -self.y)

    def __abs__(self):
        return Vec2d(abs(self.x), abs(self.y))

    def __eq__(self, other):
        return isinstance(other, Vec2d) and \
            math.isclose(self.x, other.x) and \
            math.isclose(self.y, other.y)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'gom.Vec2d ({x}, {y})'.format(x=self.x, y=self.y)

    def __json__(self):
        return {'x': self.x, 'y': self.y}

    def __api_json__(self):
        return {'$type': 'V2', 'x': self.x, 'y': self.y}

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def dot(self, other):
        assert isinstance(other, Vec2d)
        return self.x * other.x + self.y * other.y

    def norm(self):
        return self / self.length()

    def angle(self, other):
        return math.acos(self.norm() * other.norm())

    @staticmethod
    def from_params(params):
        return Vec2d(x=params['x'], y=params['y'])


class Vec3d:
    '''
    Fast wrapper for the gom.Vec3d class
    '''

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __getattribute__(self, key):
        if key == '__doc__':
            return gom.__common__.__connection__.request(Request.DOC,
                                                         {'object': self})
        return object.__getattribute__(self, key)

    def __add__(self, other):
        assert isinstance(other, Vec3d)
        return Vec3d(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        assert isinstance(other, Vec3d)
        return Vec3d(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        assert isinstance(other, Vec3d) or isinstance(other, float) or isinstance(other, int)
        if isinstance(other, Vec3d):
            return self.x * other.x + self.y * other.y + self.z * other.z

        return Vec3d(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other):
        assert isinstance(other, float) or isinstance(other, int)
        return Vec3d(self.x / other, self.y / other, self.z / other)

    def __neg__(self):
        return Vec3d(-self.x, -self.y, -self.z)

    def __abs__(self):
        return Vec3d(abs(self.x), abs(self.y), abs(self.z))

    def __eq__(self, other):
        return isinstance(other, Vec3d) and \
            math.isclose(self.x, other.x) and \
            math.isclose(self.y, other.y) and \
            math.isclose(self.z, other.z)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'gom.Vec3d ({x}, {y}, {z})'.format(x=self.x, y=self.y, z=self.z)

    def __json__(self):
        return {'x': self.x, 'y': self.y, 'z': self.z}

    def __api_json__(self):
        return {'$type': 'V3', 'x': self.x, 'y': self.y, 'z': self.z}

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def norm(self):
        return self / self.length()

    def dot(self, other):
        assert isinstance(other, Vec3d)
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Vec3d(self.y * other.z - self.z * other.y,
                     self.z * other.x - self.x * other.z,
                     self.x * other.y - self.y * other.x)

    @staticmethod
    def from_params(params):
        return Vec3d(x=params['x'], y=params['y'], z=params['z'])


class Resource:
    '''
    Representation of a file resource.

    This class is a representation of one resource imported to the GOM software.
    It can belong to a package, or be imported or linked to the software instance.
    '''

    __opened_resources = []

    @staticmethod
    def list():
        return gom.api.script_resources.list()

    @staticmethod
    def cleanup():
        # Closing all dangling resources (API call to free memory on C++ side)
        for resource in Resource.__opened_resources:
            resource.close()

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        Resource.__opened_resources.append(instance)
        return instance

    def __init__(self, path):
        """Constructor"""
        self._path = path
        self._mem_key = ""
        self._mem_size = 0
        self._mem_lock = False
        self._mm = None

    def __del__(self):
        self.close()
        Resource.__opened_resources.remove(self)
        # print ("Destructor call")

    def __exit__(self, ext_type, exc_value, traceback):
        self.close()

    def __repr__(self):
        return "Resource (%s)" % \
            (self._path)

    def __str__(self):
        return "(%s, %s bytes)" % \
            (self._path, self._mem_size)

    def _load(self, size):
        """Load resource into shared memory"""
        valid = gom.api.script_resources.create(self._path)
        if valid == False:
            raise RuntimeError('Cannot load resource "{name}". Invalid path.'.format(name=self._path))
        self._mem_key = gom.api.script_resources.load(self._path, size)
        self._mem_size = gom.api.script_resources.mem_size(self._path)

    def isLoaded(self):
        return (self._mem_key != "")

    def close(self):
        """Release resource from shared memory"""
        if self._mm is not None:
            self._mm.close()
            self._mm = None
        if not self._mem_lock:
            gom.api.script_resources.unload(self._path)
            # print ("close ", self)
            self._mem_key = ""

    def open(self, size=0):
        self._load(size)
        if self._mem_key == "":
            raise RuntimeError('Cannot open memory for resource "{name}"'.format(name=self._path))

        self._mm = mmap.mmap(-1, self._mem_size, tagname=self._mem_key, access=mmap.ACCESS_WRITE)
        self._mm.seek(0)
        return self._mm

    def exists(self):
        return gom.api.script_resources.exists(self._path)

    def byteSize(self):
        return self._mem_size

    def keepInMemory(self):
        self._mem_lock = True

    def save(self, size=0):
        success = gom.api.script_resources.save(self._path, size)
        return success

    def saveAsUserResource(self, new_path, overwrite=True):
        success = gom.api.script_resources.save_as(self._path, new_path, overwrite)
        return success


class __Testing__:

    @staticmethod
    def test0(params):
        return gom.__common__.__connection__.request(Request.TEST_0, params)

    def test1(params):
        return gom.__common__.__connection__.request(Request.TEST_1, params)

    def test2(params):
        return gom.__common__.__connection__.request(Request.TEST_2, params)

    def test3(params):
        return gom.__common__.__connection__.request(Request.TEST_3, params)

    def test4(params):
        return gom.__common__.__connection__.request(Request.TEST_4, params)

    def test5(params):
        return gom.__common__.__connection__.request(Request.TEST_5, params)


#
# Stream for unfiltered console outputs (for test script purposes)
#
console = gom.__tools__.Console()

#
# Global items as entry points into the applications object and command tree
#
app = Item('gom.app')
script = Command.create_overload_group('gom.script')
interactive = Command.create_overload_group('gom.interactive')
test = gom.__test__.TestInterface()

#
# Explicit definitions needed to be able to register override functions for the kiosk test scripts
#
script.sys = Command.create_overload_group('gom.script.sys')
interactive.sys = Command.create_overload_group('gom.interactive.sys')
script.automation = Command.create_overload_group('gom.script.automation')
interactive.automation = Command.create_overload_group('gom.interactive.automation')
script.atos = Command.create_overload_group('gom.script.atos')
interactive.atos = Command.create_overload_group('gom.interactive.atos')
script.calibration = Command.create_overload_group('gom.script.calibration')
interactive.calibration = Command.create_overload_group('gom.interactive.calibration')

#
# Register system hooks and handler
#
__import_hook_finder__ = gom.__tools__.ImportHookFinder()
__import_hook_finder__.register_hook('numpy', gom.Array.numpy_imported_hook)

sys.meta_path.insert(0, __import_hook_finder__)
sys.meta_path.append(gom.__tools__.ResourceImportFinder())

__stdout_flusher__ = gom.__tools__.StdoutFlusher()
__stdout_flusher__.__enter__()

__stderr_flusher__ = gom.__tools__.StderrFlusher()
__stderr_flusher__.__enter__()

__environment_listener__ = gom.__tools__.EnvironmentListener()
__environment_listener__.__enter__()

__exit_handler__ = gom.__tools__.ExitHandler()
__exit_handler__.__enter__()

#
# Logging facilities. When using the logger via 'gom.log.[debug|info|warning|error|fatal]', the logged
# message is passed to the application and will be persisted in a log file if the executed script setup
# supports this. This is especially valid for services, which are running in the background and do not
# have any console access.
#
__log_handler__ = gom.__tools__.LogHandler()
__log_handler__.setLevel(logging.DEBUG)

log = logging.getLogger('custom')
log.setLevel(logging.DEBUG)
log.addHandler(__log_handler__)

atexit.register(gom.Resource.cleanup)


def apifunction(func):
    '''
    Decorator for API functions

    This decorator is used to export functions from the 'gom' module to the API. The function is
    added to the 'gom.api' module and is accessible via the 'gom.api' namespace. When registered,
    it will be available for the introspection and documentation system and can be called from 
    other modules.
    '''
    gom.__api__.__api_registry__.register_function(func)


def apicontribution(contribution):
    '''
    Decorator for API contributions

    A contribution is a class derived from 'gom.__common__.Contribution' which extends some application
    specific mechanism. 

    @param contribution Contribution class definition to register into the API
    '''
    gom.__api__.__api_registry__.register_contribution(contribution)


def run_api(name=None, endpoint=None):
    '''
    Run this script as an API

    If called, the script will be executed as an API. This means that interpreter executing this script
    will be connected to the GOM application and will provide the API functions to the application. The
    function will not return until the application requests the script to terminate.

    @attention Pass the 'name' and 'endpoint' parameter *only* for debugging purposes ! See documentation for details.

    @param name     Service name. This is mainly a debugging feature at the moment and is usually not specified
                    but read from the services 'metainfo.json' entry.
    @param endpoint Service API endpoint. This is mainly a debugging feature at the moment and is usually not specified
                    but read from the services 'metainfo.json' entry.
    '''
    gom.log.info(f'Service starting')

    gom.__common__.__connection__.request(
        Request.RUNAPI, {'declaration': gom.__api__.__api_registry__.get_declaration(),
                         'name': name if name else '', 'endpoint': endpoint if endpoint else ''})

    gom.log.info(f'Service shutdown')


def read_parameters(container):
    '''
    Read explicit script calling parameters into a given container

    @attention THIS FUNCTION USES AN OBSOLETE FEATURE !

    In the past if was possible to set the global parameters of a called script from the caller. This
    feature has been abandoned, but can still be used for compatibility reasons. It is strongly recommended
    to use another approach like explicit function calling or the service API instead.

    @param container Dictionary where the parameters should be added
    @return 'True' when parameters have been passed
    '''
    configuration = gom.__common__.__connection__.request(Request.CONFIGURATION, {})

    if 'parameters' in configuration:
        container.update(configuration['parameters'])
        return True

    return False


#
# MAIN
#
# If the environment variable 'TOM_PYTHON_API_URL' is set, the module will connect to a running
# ZEISS inspect application instance. This is the case if the script is started from within an
# application as a local script automatically.
#
# Example: set TOM_PYTHON_API_URL="ws://localhost:41000?key=656bd8a17823f8e54bd2"
#
__server_url_var__ = 'TOM_PYTHON_API_URL'
__api_url__ = None

if __server_url_var__ in os.environ:
    #
    # Connection URL to the python interpreter is given directly. This is the case if the script has been
    # started from within the ZEISS Inspect application itself.
    #
    __api_url__ = os.environ[__server_url_var__]

if gom.__config__.server_url is None and not __api_url__ is None:
    url = urllib.parse.urlparse(__api_url__)
    queries = urllib.parse.parse_qs(url.query)

    gom.__config__.server_url = __api_url__
    gom.__config__.strip_tracebacks = int(queries['strip_tracebacks'][0]) > 0 if 'strip_tracebacks' in queries else True

    if 'interpreter_id' in queries:
        gom.__config__.interpreter_id = queries['interpreter_id'][0]
    else:
        gom.__config__.interpreter_id = str(uuid.uuid4())

    if 'apikey' in queries:
        gom.__config__.api_access_key = queries['apikey'][0]

    import gom.__network__

    #
    # Find frame of the topmost script to be able to register its filename for relative imports and
    # resources accesses. A special case are external debuggers: These are wrapping the called script
    # into a debugging framework. This is usually 'debugpy', so the frame filtering will respect this
    # debugging environment explicitly and detect the topmost frame which is not part of the debugging
    # environment.
    #
    frame = inspect.currentframe()

    top_filename = None
    top_frame = frame

    while frame:
        filename = frame.f_globals['__file__'].replace('\\', '/') if '__file__' in frame.f_globals else ''

        if not '/debugpy/' in filename:
            top_filename = filename
            top_frame = frame
            frame = frame.f_back
        else:
            frame = None

    gom.__common__.__connection__ = gom.__network__.Connection(uri=gom.__config__.server_url)
    configuration = gom.__common__.__connection__.request(
        Request.REGISTER, {'id': gom.__config__.interpreter_id, 'file': top_filename})

    if 'interpreter_id' in queries:
        sys.excepthook = gom.__tools__.__excepthook__

    if 'path' in configuration:
        for p in configuration['path']:
            sys.path.append(p)

    if top_frame and 'parameters' in configuration:
        top_frame.f_globals.update(configuration['parameters'])

    #
    # Query remote object types which are available via script interface instances
    #
    object_types = gom.__common__.__connection__.request(Request.OBJECTTYPES, {})

    for type_id, type_name in object_types.items():
        type_obj = gom.__types__.Types.register_type(type_id, type_name)
        if type_obj:
            gom.__dict__[type_name] = type_obj

    #
    # For API functions which are officially documented, a 'real' API module is created. For all
    # other modules, a generic access mechanism which queries API modules and functions dynamically
    # has to be established.
    #
    for module in gom.api.introspection.modules():
        name = module.name()
        spec = importlib.util.find_spec(f'gom.api.{name}')
        if not spec:
            gom.api.__dict__[name] = gom.__api__.GomApiRoot(name)

else:
    warnings.warn(
        f' No connection to a running ZEISS Inspect application configured, please set {__server_url_var__} accordingly')
