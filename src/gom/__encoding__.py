#
# encoding.py - Encodings for communication with the application via sockets
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

import base64
import functools
import json
import mmap
import os
import struct
import sys

import gom
from gom.__types__ import Types
from enum import Enum


class Encoder:
    '''
    Encoder base class
    '''

    class PackageType (Enum):
        '''
        \brief Package content data type
        \attention Must match with the enumeration in the server
        '''
        INVALID = 0
        INT_8 = 1
        INT_16 = 2
        INT_32 = 3
        INT_64 = 4
        UINT_8 = 5
        UINT_16 = 6
        UINT_32 = 7
        UINT_64 = 8
        FLOAT_32 = 9
        FLOAT_64 = 10

    numpy_supported = None
    shared_memory_id_counter = 0

    @staticmethod
    def supports_numpy():
        if Encoder.numpy_supported is None:

            try:
                global np
                import numpy as np
                Encoder.numpy_supported = True
            except ImportError as e:
                Encoder.numpy_supported = False

        return Encoder.numpy_supported

    @staticmethod
    def supports_shared_memory():
        return sys.platform.startswith('win')

    @staticmethod
    def read_from_shared_memory(key, shape, dtype, context):

        size = np.prod(shape, dtype=np.int64)

        if not Encoder.supports_shared_memory():
            raise RuntimeError('Shared memory is not supported on platform \'{name}\''.format(name=sys.platform))

        supported_types = [np.int8, np.int16, np.int32, np.int64, np.uint8,
                           np.uint16, np.uint32, np.uint64, np.float32, np.float64]
        if dtype not in supported_types:
            raise RuntimeError('Unsupported data type \'{type}\'. Allowed types are: [\'{types}\']'.format(
                type=dtype, types=', '.join(supported_types)))

        byte_size = size * np.dtype(dtype).itemsize
        with mmap.mmap(-1, byte_size, tagname=key, access=mmap.ACCESS_READ) as m:
            result = np.frombuffer(bytes(m[:]), dtype=dtype, count=size).reshape(shape)

        context.add(key)

        return result

    @staticmethod
    def create_shared_memory_segment(data):

        segment = None
        key = None

        if Encoder.supports_shared_memory():
            b = data.tobytes(order='C')

            key = 'GScriptSHMEM/Client/{pid}/{id}'.format(pid=os.getpid(), id=Encoder.shared_memory_id_counter)
            Encoder.shared_memory_id_counter += 1

            segment = mmap.mmap(-1, len(b), tagname=key, access=mmap.ACCESS_WRITE)

            segment.write(b)
            segment.flush()
        else:
            raise RuntimeError('Shared memory is not supported on platform \'{name}\''.format(name=sys.platform))

        return segment, key


class CdcEncoder (Encoder):
    '''
    Class for encoding/decoding payload data in CDC (compact data container) format
    '''

    class Type (Enum):
        '''
        \brief Data types handled by the CDC encoding scheme.
        \attention Must match with the enumeration in the server
        '''
        NONE = 0
        BOOLEAN = 1
        INTEGER = 2
        FLOAT = 3
        STRING = 4
        LIST = 5
        MAP = 6
        SLICE = 7
        ITEM = 8
        INDEXABLE = 9
        COMMAND = 10
        CALLABLE = 11
        ERROR = 12
        TRAIT = 13
        OBJECT = 14
        ARRAY = 15
        PACKAGE = 16
        VEC2D = 17
        VEC3D = 18
        RESOURCE_ACCESS = 19
        BLOB = 20

    def encode(self, obj, context):
        '''
        \brief Encode data package

        Encodes an arbitrary Python object into binary payload package.
        \param obj	 Python object
        \param context Context for additional encoding information like used shared memory segments etc.
        \return Binary data block
        '''
        buffer = bytearray()
        self.encodeValue(buffer, obj, context)
        return buffer

    def encodeValue(self, buffer, obj, context):
        '''
        \brief Encode object into CDC (compact data container) format

        \param buffer Array chunk buffer the generated data is appended to
        \param obj	Arbitrary Python object to be encoded
        '''
        if obj is None:
            self.encodeType(buffer, CdcEncoder.Type.NONE)

        elif isinstance(obj, bool):
            self.encodeType(buffer, CdcEncoder.Type.BOOLEAN)
            self.encodeBool(buffer, obj)

        elif isinstance(obj, int):
            self.encodeType(buffer, CdcEncoder.Type.INTEGER)
            self.encodeInt(buffer, obj)

        elif isinstance(obj, float):
            self.encodeType(buffer, CdcEncoder.Type.FLOAT)
            self.encodeFloat(buffer, obj)

        elif isinstance(obj, str):
            self.encodeType(buffer, CdcEncoder.Type.STRING)
            self.encodeStr(buffer, obj)

        elif isinstance(obj, list) or isinstance(obj, tuple):
            self.encodeType(buffer, CdcEncoder.Type.LIST)
            self.encodeInt(buffer, len(obj))
            for i in obj:
                self.encodeValue(buffer, i, context)

        elif isinstance(obj, dict):
            self.encodeType(buffer, CdcEncoder.Type.MAP)
            self.encodeInt(buffer, len(obj))
            for k, v in obj.items():
                self.encodeStr(buffer, k)
                self.encodeValue(buffer, v, context)

        elif isinstance(obj, slice):
            self.encodeType(buffer, CdcEncoder.Type.SLICE)
            self.encodeValue(buffer, obj.start, context)
            self.encodeValue(buffer, obj.stop, context)

        elif isinstance(obj, gom.Item):
            self.encodeType(buffer, CdcEncoder.Type.ITEM)
            self.encodeStr(buffer, obj.__id__)
            self.encodeInt(buffer, obj.__category__)
            self.encodeInt(buffer, obj.__stage__)

        elif isinstance(obj, gom.Indexable):
            self.encodeType(buffer, CdcEncoder.Type.INDEXABLE)
            self.encodeValue(buffer, obj.item, context)
            self.encodeStr(buffer, obj.token)
            self.encodeInt(buffer, obj.size)

        elif isinstance(obj, gom.Command):
            self.encodeType(buffer, CdcEncoder.Type.COMMAND)
            self.encodeStr(buffer, repr(obj))

        elif isinstance(obj, gom.Vec2d):
            self.encodeType(buffer, CdcEncoder.Type.VEC2D)
            self.encodeFloat(buffer, obj.x)
            self.encodeFloat(buffer, obj.y)

        elif isinstance(obj, gom.Vec3d):
            self.encodeType(buffer, CdcEncoder.Type.VEC3D)
            self.encodeFloat(buffer, obj.x)
            self.encodeFloat(buffer, obj.y)
            self.encodeFloat(buffer, obj.z)

        elif hasattr(obj, '__id__') and obj.__id__ in Types.types:
            self.encodeType(buffer, CdcEncoder.Type.TRAIT)
            self.encodeStr(buffer, obj.__id__)
            self.encodeValue(buffer, obj.__args__, context)
            self.encodeValue(buffer, obj.__kwargs__, context)

        elif isinstance(obj, functools.partial):
            self.encodeType(buffer, CdcEncoder.Type.CALLABLE)
            self.encodeStr(buffer, Types.get_id_for_object(obj))
            self.encodeStr(buffer, obj.func.__module__ + '.' + obj.func.__name__)

        elif callable(obj):
            self.encodeType(buffer, CdcEncoder.Type.CALLABLE)
            self.encodeStr(buffer, Types.get_id_for_object(obj))
            self.encodeStr(buffer, obj.__module__ + '.' + obj.__name__)

        elif isinstance(obj, gom.Array):
            self.encodeType(buffer, CdcEncoder.Type.ARRAY)
            self.encodeValue(buffer, obj.project, context)
            self.encodeValue(buffer, obj.item, context)
            self.encodeStr(buffer, obj.key)
            self.encodeValue(buffer, obj.index, context)
            self.encodeBool(buffer, obj.selected)
            self.encodeValue(buffer, obj.transformation, context)

        elif isinstance(obj, gom.ResourceAccess):
            self.encodeType(buffer, CdcEncoder.Type.RESOURCE_ACCESS)

        elif isinstance(obj, bytes):
            self.encodeType(buffer, CdcEncoder.Type.BLOB)
            self.encodeInt(buffer, len(obj))
            buffer.extend(obj)

        elif Encoder.supports_numpy() and isinstance(obj, np.ndarray):
            if obj.size == 0:
                raise RuntimeError('Array is empty and cannot be encoded')

            self.encodeType(buffer, CdcEncoder.Type.PACKAGE)
            self.encodeInt(buffer, len(obj.shape))

            for i in obj.shape:
                self.encodeInt(buffer, i)

            if obj.dtype == np.int8:
                self.encodeInt(buffer, Encoder.PackageType.INT_8.value)
            elif obj.dtype == np.int16:
                self.encodeInt(buffer, Encoder.PackageType.INT_16.value)
            elif obj.dtype == np.int32:
                self.encodeInt(buffer, Encoder.PackageType.INT_32.value)
            elif obj.dtype == np.int64:
                self.encodeInt(buffer, Encoder.PackageType.INT_64.value)
            elif obj.dtype == np.uint8:
                self.encodeInt(buffer, Encoder.PackageType.UINT_8.value)
            elif obj.dtype == np.uint16:
                self.encodeInt(buffer, Encoder.PackageType.UINT_16.value)
            elif obj.dtype == np.uint32:
                self.encodeInt(buffer, Encoder.PackageType.UINT_32.value)
            elif obj.dtype == np.uint64:
                self.encodeInt(buffer, Encoder.PackageType.UINT_64.value)
            elif obj.dtype == np.float32:
                self.encodeInt(buffer, Encoder.PackageType.FLOAT_32.value)
            elif obj.dtype == np.float64:
                self.encodeInt(buffer, Encoder.PackageType.FLOAT_64.value)
            else:
                raise RuntimeError(
                    '\'{obj}\' has unsupported data type \'{type}\'and cannot be encoded'.format(obj=obj, type=obj.dtype))

            if Encoder.supports_shared_memory():
                self.encodeBool(buffer, True)
                segment, key = Encoder.create_shared_memory_segment(obj)

                context.add(segment)
                self.encodeStr(buffer, key)

            else:
                self.encodeBool(buffer, False)

                buffer.extend(obj.tobytes())

        else:
            raise RuntimeError(
                '\'{obj}\' has unsupported type \'{type}\'and cannot be encoded'.format(obj=obj, type=type(obj)))

    def encodeType(self, buffer, obj):
        buffer.extend(struct.pack('b', obj.value))

    def encodeBool(self, buffer, obj):
        buffer.extend(struct.pack('b', 1 if obj else 0))

    def encodeByte(self, buffer, obj):
        buffer.extend(struct.pack('B', obj))

    def encodeInt(self, buffer, obj):
        buffer.extend(struct.pack('q', obj))

    def encodeFloat(self, buffer, obj):
        buffer.extend(struct.pack('d', obj))

    def encodeStr(self, buffer, obj):
        s = obj.encode('utf-8')
        self.encodeInt(buffer, len(s))
        buffer.extend(s)

    def decode(self, data, context):
        '''
        \brief Decode data package

        \param data Binary data block
        \return Represented Python object
        '''
        class InStream:

            def __init__(self, data):
                self.data = data
                self.index = 0

            def read(self, n):
                d = self.data[self.index:self.index + n]
                self.index += n
                return d

        value = self.decodeValue(InStream(data), context)
        return value

    def decodeValue(self, s, context):
        '''
        \brief Decode the next encoded Python object in the buffer

        If the encoded object is a container, the container content is decoded
        recursively.

        \param s Data stream
        \return Python object
        '''
        obj_type = CdcEncoder.Type(s.read(1)[0])

        if obj_type == CdcEncoder.Type.NONE:
            return None

        elif obj_type == CdcEncoder.Type.BOOLEAN:
            return struct.unpack('b', s.read(1))[0] != 0

        elif obj_type == CdcEncoder.Type.INTEGER:
            return self.decodeInt(s)

        elif obj_type == CdcEncoder.Type.FLOAT:
            return self.decodeFloat(s)

        elif obj_type == CdcEncoder.Type.STRING:
            return self.decodeStr(s)

        elif obj_type == CdcEncoder.Type.LIST:
            size = self.decodeInt(s)
            return [self.decodeValue(s, context) for _ in range(size)]

        elif obj_type == CdcEncoder.Type.MAP:
            size = self.decodeInt(s)

            m = {}

            for _ in range(size):
                key = self.decodeStr(s)
                value = self.decodeValue(s, context)
                m[key] = value

            return m

        elif obj_type == CdcEncoder.Type.SLICE:
            start = self.decodeValue(s, context)
            stop = self.decodeValue(s, context)

            return slice(start, stop)

        elif obj_type == CdcEncoder.Type.ITEM:
            id = self.decodeStr(s)
            category = self.decodeInt(s)
            stage = self.decodeInt(s)
            return gom.Item(id, category, stage)

        elif obj_type == CdcEncoder.Type.INDEXABLE:
            item = self.decodeValue(s, context)
            token = self.decodeStr(s)
            size = self.decodeInt(s)

            return gom.Indexable(item, token, size)

        elif obj_type == CdcEncoder.Type.COMMAND:
            name = self.decodeStr(s)
            return gom.Command(name)

        elif obj_type == CdcEncoder.Type.CALLABLE:
            object_id = self.decodeStr(s)
            description = self.decodeStr(s)
            return Types.get_object_for_id(object_id)

        elif obj_type == CdcEncoder.Type.ERROR:
            id = self.decodeStr(s)
            text = self.decodeStr(s)
            line = self.decodeInt(s)

            return None

        elif obj_type == CdcEncoder.Type.VEC2D:
            x = self.decodeFloat(s)
            y = self.decodeFloat(s)

            return gom.Vec2d(x, y)

        elif obj_type == CdcEncoder.Type.VEC3D:
            x = self.decodeFloat(s)
            y = self.decodeFloat(s)
            z = self.decodeFloat(s)

            return gom.Vec3d(x, y, z)

        elif obj_type == CdcEncoder.Type.TRAIT:
            id = self.decodeStr(s)
            args = self.decodeValue(s, context)
            kwargs = self.decodeValue(s, context)

            return Types.create_object(id, args, kwargs)

        elif obj_type == CdcEncoder.Type.OBJECT:
            return gom.Object.from_params(self.decodeValue(s, context))

        elif obj_type == CdcEncoder.Type.ARRAY:
            project = self.decodeValue(s, context)
            item = self.decodeValue(s, context)
            key = self.decodeStr(s)
            index = self.decodeValue(s, context)
            selected = self.decodeBool(s)
            transformation = self.decodeValue(s, context)
            return gom.Array(project=project, item=item, key=key, index=index,
                             selected=selected, transformation=transformation)

        elif obj_type == CdcEncoder.Type.RESOURCE_ACCESS:
            return gom.ResourceAccess()

        elif obj_type == CdcEncoder.Type.BLOB:
            size = self.decodeInt(s)
            return s.read(size)

        elif obj_type == CdcEncoder.Type.PACKAGE:

            if not Encoder.supports_numpy():
                raise RuntimeError('Numpy is not supported')

            dims = self.decodeInt(s)
            shape = [self.decodeInt(s) for _ in range(dims)]
            data_type = Encoder.PackageType(self.decodeInt(s))
            use_shared_memory = self.decodeBool(s)

            dtype = None

            if data_type == Encoder.PackageType.INT_8:
                dtype = np.int8
            elif data_type == Encoder.PackageType.INT_16:
                dtype = np.int16
            elif data_type == Encoder.PackageType.INT_32:
                dtype = np.int32
            elif data_type == Encoder.PackageType.INT_64:
                dtype = np.int64
            elif data_type == Encoder.PackageType.UINT_8:
                dtype = np.uint8
            elif data_type == Encoder.PackageType.UINT_16:
                dtype = np.uint16
            elif data_type == Encoder.PackageType.UINT_32:
                dtype = np.uint32
            elif data_type == Encoder.PackageType.UINT_64:
                dtype = np.uint64
            elif data_type == Encoder.PackageType.FLOAT_32:
                dtype = np.float32
            elif data_type == Encoder.PackageType.FLOAT_64:
                dtype = np.float64
            else:
                raise RuntimeError('Unsupported package type')

            if use_shared_memory:
                key = self.decodeStr(s)
                return Encoder.read_from_shared_memory(key, shape, dtype, context)

            size = int(np.prod(shape))
            b = bytes(s.read(size * np.dtype(dtype).itemsize))
            return np.frombuffer(b, dtype=dtype, count=size).reshape(shape)

        return None

    def decodeBool(self, s):
        return struct.unpack('b', s.read(1))[0] != 0

    def decodeInt(self, s):
        return struct.unpack('q', s.read(8))[0]

    def decodeFloat(self, s):
        return struct.unpack('d', s.read(8))[0]

    def decodeStr(self, s):
        size = self.decodeInt(s)
        return bytes(s.read(size)).decode('utf-8')


# ----------------------------------------------------------------------------
# CLASS gom.JsonEncoder
#
# Payload data encoding/decoding in JSON format
#
class JsonEncoder (Encoder):
    '''
    \brief Payload data encoding/decoding in JSON format
    '''

    #
    # If an incoming map contains this key, the underlying type is not a regular dictionary, but
    # represents the definition of a generic trait type. It is assumed that the dictionary in this
    # case contains all information required to reconstruct the type in question.
    #
    TYPE_DEFINITION_KEY = '__TOM_TYPE_DEFINITION__'

    #
    # Type names for mapping a C++ type onto its Python equivalent and vice versa
    #
    TYPE_BLOB = 'Tom::GScript::Blob'
    TYPE_CALLABLE = 'Tom::GScript::Callable'
    TYPE_COMMAND = 'Tom::GScript::Command'
    TYPE_ARRAY = 'Tom::GScript::Array'
    TYPE_INDEXABLE = 'Tom::GScript::Indexable'
    TYPE_ITEM = 'Tom::GScript::Item'
    TYPE_OBJECT = 'Tom::GScript::Object'
    TYPE_RESOURCE_ACCESS = 'Tom::GScript::ResourceAccess'
    TYPE_PACKAGE = 'Tom::DataInterface::Package'
    TYPE_SLICE = 'Tom::ScriptTypeInterface::Slice'
    TYPE_VEC2D = 'Tom::Vec2d'
    TYPE_VEC3D = 'Tom::Vec3d'

    class_ids = {gom.Indexable: TYPE_INDEXABLE,
                 gom.Item: TYPE_ITEM,
                 gom.ResourceAccess: TYPE_RESOURCE_ACCESS,
                 gom.Command: TYPE_COMMAND,
                 gom.Vec2d: TYPE_VEC2D,
                 gom.Vec3d: TYPE_VEC3D}

    def encode(self, obj, context):
        '''
        \brief Encode data package

        Encodes an arbitrary Python object into binary payload package.

        \param obj Python object
        \return Binary data block
        '''
        return json.dumps(JsonEncoder.encode_traits(obj, context)).encode()

    def decode(self, data, context):
        '''
        Decode data package

        This function decodes a binary payload data package into the represented
        Python object.

        \param data Binary data block
        \return Python object
        '''
        return JsonEncoder.decode_traits(json.loads(data.decode()), context)

    @staticmethod
    def encode_traits(obj, context):
        '''
        \brief Encode complex Python types into JSON compatible format

        In JSON there is no way to transmit other than the standard objects (bool, int, ..., list, map).
        So types like Item or dynamically registeres types must be converted into a map like representation
        before being encoded.

        \param obj	 Python object to be encoded
        \param context Encoding context for keeping addition information like the used shared memory segements
        \return Python object with complex data types converted into a map like representation
        '''

        if hasattr(obj, '__json__'):
            params = {k: JsonEncoder.encode_traits(v, context) for k, v in obj.__json__().items()}

            if type(obj) in JsonEncoder.class_ids:
                params[JsonEncoder.TYPE_DEFINITION_KEY] = JsonEncoder.class_ids[type(obj)]
            elif Types.is_registered_type(type(obj)):
                params[JsonEncoder.TYPE_DEFINITION_KEY] = obj.__id__
            else:
                raise RuntimeError('object does not have a valid type for JSON encoding')

            return JsonEncoder.encode_traits(params, context)

        elif isinstance(obj, list):
            return [JsonEncoder.encode_traits(i, context) for i in obj]

        elif isinstance(obj, dict):
            return {key: JsonEncoder.encode_traits(value, context) for key, value in obj.items()}

        elif isinstance(obj, slice):
            return {JsonEncoder.TYPE_DEFINITION_KEY: JsonEncoder.TYPE_SLICE,
                    'start': JsonEncoder.encode_traits(obj.start, context),
                    'stop': JsonEncoder.encode_traits(obj.stop, context)}

        elif isinstance(obj, bytes):
            return {JsonEncoder.TYPE_DEFINITION_KEY: JsonEncoder.TYPE_BLOB,
                    'data': str(base64.encodebytes(obj), 'utf-8')}

        elif callable(obj):
            return {JsonEncoder.TYPE_DEFINITION_KEY: JsonEncoder.TYPE_CALLABLE,
                    'id': Types.get_id_for_object(obj),
                    'name': repr(obj)}

        elif Encoder.supports_numpy() and isinstance(obj, np.ndarray):
            try:
                type = {np.int8: Encoder.PackageType.INT_8.value,
                        np.int16: Encoder.PackageType.INT_16.value,
                        np.int32: Encoder.PackageType.INT_32.value,
                        np.int64: Encoder.PackageType.INT_64.value,
                        np.uint8: Encoder.PackageType.UINT_8.value,
                        np.uint16: Encoder.PackageType.UINT_16.value,
                        np.uint32: Encoder.PackageType.UINT_32.value,
                        np.uint64: Encoder.PackageType.UINT_64.value,
                        np.float32: Encoder.PackageType.FLOAT_32.value,
                        np.float64: Encoder.PackageType.FLOAT_64.value}[obj.dtype]
            except KeyError:
                raise RuntimeError('Unsupported numpy array type \'{type}\'').arg(obj.dtype)

            if Encoder.supports_shared_memory():
                segment, key = Encoder.create_shared_memory_segment(obj)
                context.add(segment)
                return {JsonEncoder.TYPE_DEFINITION_KEY: JsonEncoder.TYPE_PACKAGE,
                        'shape': list(obj.shape),
                        'type': type,
                        'key': key}
            else:
                if obj.dtype == np.float64:

                    return {JsonEncoder.TYPE_DEFINITION_KEY: JsonEncoder.TYPE_PACKAGE,
                            'shape': list(obj.shape),
                            'type': type,
                            'data': [float(i) for i in obj.reshape((obj.size))]}
                else:
                    return {JsonEncoder.TYPE_DEFINITION_KEY: JsonEncoder.TYPE_PACKAGE,
                            'shape': list(obj.shape),
                            'type': type,
                            'data': [int(i) for i in obj.reshape((obj.size))]}
        return obj

    @staticmethod
    def decode_traits(obj, context):
        '''
        Decode complex Python type from intermediate Python map representation

        When an object is received from the application, it already has been decoded from payload format
        into native Python objects. This function is then called to convert the dictionary objects
        which are representing dynamic types into these types.

        \param obj Python object in decoded format
        \return Python object with all intermediate types resolved
        '''

        result = None

        #
        # Lists are processed recursively
        #
        if isinstance(obj, list):
            result = [JsonEncoder.decode_traits(i, context) for i in obj]

        #
        # A map can either be a plain oldschool Python map, represent a dynamically registered
        # type or a special object like an item or a command.
        #
        elif isinstance(obj, dict):
            params = {k: JsonEncoder.decode_traits(v, context) for k, v in obj.items()}

            if JsonEncoder.TYPE_DEFINITION_KEY in params:
                type_id = params[JsonEncoder.TYPE_DEFINITION_KEY]

                if type_id == 'Tom::Value::Error':
                    result = None
                elif type_id == JsonEncoder.TYPE_SLICE:
                    result = slice(params['start'], params['stop'])
                elif type_id == JsonEncoder.TYPE_ITEM:
                    result = gom.Item.from_params(params)
                elif type_id == JsonEncoder.TYPE_INDEXABLE:
                    result = gom.Indexable.from_params(params)
                elif type_id == JsonEncoder.TYPE_COMMAND:
                    result = gom.Command.from_params(params)
                elif type_id == JsonEncoder.TYPE_CALLABLE:
                    result = Types.get_object_for_id(params['id'])
                elif type_id == JsonEncoder.TYPE_OBJECT:
                    result = gom.Object.from_params(params['data'])
                elif type_id == JsonEncoder.TYPE_ARRAY:
                    result = gom.Array.from_params(params)
                elif type_id == JsonEncoder.TYPE_RESOURCE_ACCESS:
                    result = gom.ResourceAccess.from_params(params)
                elif type_id == JsonEncoder.TYPE_VEC2D:
                    result = gom.Vec2d.from_params(params)
                elif type_id == JsonEncoder.TYPE_VEC3D:
                    result = gom.Vec3d.from_params(params)
                elif type_id == JsonEncoder.TYPE_BLOB:
                    result = base64.decodebytes(bytes(params['data'], 'utf-8'))
                elif type_id == JsonEncoder.TYPE_PACKAGE:

                    if not Encoder.supports_numpy():
                        raise RuntimeError('Numpy is not supported')

                    type = Encoder.PackageType(params['type'])

                    dtype = None
                    if type == Encoder.PackageType.INT_8:
                        dtype = np.int8
                    elif type == Encoder.PackageType.INT_16:
                        dtype = np.int16
                    elif type == Encoder.PackageType.INT_32:
                        dtype = np.int32
                    elif type == Encoder.PackageType.INT_64:
                        dtype = np.int64
                    elif type == Encoder.PackageType.UINT_8:
                        dtype = np.uint8
                    elif type == Encoder.PackageType.UINT_16:
                        dtype = np.uint16
                    elif type == Encoder.PackageType.UINT_32:
                        dtype = np.uint32
                    elif type == Encoder.PackageType.UINT_64:
                        dtype = np.uint64
                    elif type == Encoder.PackageType.FLOAT_32:
                        dtype = np.float32
                    elif type == Encoder.PackageType.FLOAT_64:
                        dtype = np.float64
                    else:
                        raise RuntimeError('Unsupported data type')

                    if 'key' in params:
                        result = Encoder.read_from_shared_memory(params['key'], params['shape'], dtype, context)
                    else:
                        result = np.array(params['data'], dtype=dtype).reshape(params['shape'])

                elif type_id in Types.types:
                    result = Types.create_object(type_id, params['args'], params['kwargs'])
                else:
                    raise RuntimeError('Type \'{typeid}\' is not a registered type'.format(typeid=type_id))

            else:
                result = params

        else:
            result = obj

        return result
