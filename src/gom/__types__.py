#
# types.py - Type related classes
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

import gom.__common__
from gom.__common__ import Request

#
# Types which are handled by special local classes although having a valid script type interface
#
LOCAL_TYPES = ['Core::Types::BaVec<3,double>', 'Core::Types::BaVec<2,double>']


# ----------------------------------------------------------------------------
# CLASS gomlib.types.Types
#
# Dynamic type administration and handling instance.
#
# This class is used to create and instantiate new Python types which are matching
# arbitrary C++ traits. This is done in a dynamic way so that no formal type
# definition has to be transmitted between client and server.
#
class Types:

    #
    # Registered generic types (dictionary TypeId / class object)
    #
    types = {}
    type_objs = {}

    #
    # Dictionary of unique id/object
    #
    objects = {}

    #
    # Type initializing function
    #
    # This function is registered as '__init__' function for the dynamically registered types.
    #
    @staticmethod
    def type_init(self, *args, **kwargs):
        params = gom.__common__.__connection__.request(Request.TYPE_CONSTRUCT, {'type': type(self).__id__,
                                                                                'args': args,
                                                                                'kwargs': kwargs})
        self.__dict__['__args__'] = params['args']
        self.__dict__['__kwargs__'] = params['kwargs']

    #
    # Attribute requesting function for registered types
    #
    # This function is registred as '__getattr__' function for the dynamically registered types.
    #
    @staticmethod
    def type_getattr(self, key):

        if key in self.__kwargs__:
            return self.__kwargs__[key]

        return gom.__common__.__connection__.request(Request.TYPE_GETATTR, {'type': type(self).__id__,
                                                                            'args': self.__args__,
                                                                            'kwargs': self.__kwargs__,
                                                                            'name': key})

    #
    # Attribute requesting function for registered types
    #
    # This function is registred as '__getitem__' function for the dynamically registered types.
    #
    @staticmethod
    def type_getitem(self, key):
        return gom.__common__.__connection__.request(Request.TYPE_GETITEM, {'type': type(self).__id__,
                                                                            'args': self.__args__,
                                                                            'kwargs': self.__kwargs__,
                                                                            'index': key})

    #
    # Attribute requesting function for registered types
    #
    # This function is registered as '__getattribute__' function for dynamically registered types.
    # Its purpose is to handle the build-in attributes like '__doc__' which are usually statically
    # assigned for regular types.
    #
    @staticmethod
    def type_getattribute(self, key):
        if key == '__doc__':
            return gom.__common__.__connection__.request(Request.TYPE_DOC, {'type': type(self).__id__,
                                                                            'args': self.__args__,
                                                                            'kwargs': self.__kwargs__,
                                                                            'index': key})

        return object.__getattribute__(self, key)

    #
    # Attribute setting function for registered types
    #
    # This function is registered as '__setattr__' function for dynamically registered types.
    #
    @staticmethod
    def type_setattr(self, key, value):

        if key in self.__args__:
            self.__kwargs__[key] = value

        gom.__common__.__connection__.request(Request.TYPE_SETATTR, {'type': type(self).__id__,
                                                                     'args': self.__args__,
                                                                     'kwargs': self.__kwargs__,
                                                                     'name': key,
                                                                     'value': value})

    #
    # Attribute setting function for registered types
    #
    # This function is registered as '__setitem__' function for dynamically registered types.
    #
    @staticmethod
    def type_setitem(self, key, value):
        gom.__common__.__connection__.request(Request.TYPE_SETITEM, {'type': type(self).__id__,
                                                                     'args': self.__args__,
                                                                     'kwargs': self.__kwargs__,
                                                                     'key': key,
                                                                     'value': value})

    #
    # Representation generating function for registered types
    #
    # This function is registered as '__str__' function for dynamically registered types.
    #
    @staticmethod
    def type_str(self):
        return gom.__common__.__connection__.request(Request.TYPE_STR, {'type': type(self).__id__,
                                                                        'args': self.__args__,
                                                                        'kwargs': self.__kwargs__})

    #
    # Representation generating function for registered types
    #
    # This function is registered as '__repr__' function for dynamically registered types.
    #
    @staticmethod
    def type_repr(self):
        return gom.__common__.__connection__.request(Request.TYPE_REPR, {'type': type(self).__id__,
                                                                         'args': self.__args__,
                                                                         'kwargs': self.__kwargs__})

    @staticmethod
    def type_iter(self):
        elements = gom.__common__.__connection__.request(Request.TYPE_ITER, {'type': type(self).__id__,
                                                                             'args': self.__args__,
                                                                             'kwargs': self.__kwargs__})
        for e in elements:
            yield e

    @staticmethod
    def type_len(self):
        return gom.__common__.__connection__.request(Request.TYPE_LEN, {'type': type(self).__id__,
                                                                        'args': self.__args__,
                                                                        'kwargs': self.__kwargs__})

    @staticmethod
    def type_call(self, *args, **kwargs):
        return gom.__common__.__connection__.request(Request.TYPE_CALL, {'type': type(self).__id__,
                                                                         'args': self.__args__,
                                                                         'kwargs': self.__kwargs__,
                                                                         'callargs': args,
                                                                         'callkwargs': kwargs})

    @staticmethod
    def type_lt(self, other):
        return Types.compare(self, other) == 'less'

    @staticmethod
    def type_le(self, other):
        state = Types.compare(self, other)
        return state == 'less' or state == 'equal'

    @staticmethod
    def type_eq(self, other):
        if isinstance(other, str):
            return other == Types.type_str(self)

        return Types.compare(self, other) == 'equal'

    @staticmethod
    def type_ne(self, other):
        if isinstance(other, str):
            return other != Types.type_str(self)

        state = Types.compare(self, other)
        return state == 'less' or state == 'greater' or state == 'not_equal'

    @staticmethod
    def type_gt(self, other):
        return Types.compare(self, other) == 'greater'

    @staticmethod
    def type_ge(self, other):
        state = Types.compare(self, other)
        return state == 'greater' or state == 'equal'

    @staticmethod
    def type_json(self):
        return {'args': self.__args__,
                'kwargs': self.__kwargs__}

    @staticmethod
    def type_hash(self):
        return hash(Types.type_repr(self))

    @staticmethod
    def compare(self, other):
        if not Types.is_registered_type(type(self)):
            return False

        if Types.is_registered_type(type(other)):
            return gom.__common__.__connection__.request(Request.TYPE_CMP, {'type1': type(self).__id__,
                                                                            'args1': self.__args__,
                                                                            'kwargs1': self.__kwargs__,
                                                                            'type2': other.__id__,
                                                                            'args2': other.__args__,
                                                                            'kwargs2': other.__kwargs__})

        return gom.__common__.__connection__.request(Request.TYPE_CMP, {'type': type(self).__id__,
                                                                        'args': self.__args__,
                                                                        'kwargs': self.__kwargs__,
                                                                        'obj': other})

    @staticmethod
    def string_compare(self, other):
        return str(self) == other if isinstance(other, str) else False

    #
    # Create object from type definition
    #
    @staticmethod
    def create_object(type_id, args, kwargs):

        assert type_id in Types.types, f"'{type_id}' is not a registered type"

        type_obj = Types.types[type_id]
        obj = type_obj.__new__(type_obj)

        obj.__dict__['__args__'] = list(args)
        obj.__dict__['__kwargs__'] = kwargs

        return obj

    #
    # Generate unique id for the given object
    #
    @staticmethod
    def get_id_for_object(obj):
        key = str(id(obj))
        Types.objects[key] = obj
        return key

    #
    # Return object matching the unique id
    #
    @staticmethod
    def get_object_for_id(id):
        return Types.objects[id] if id in Types.objects else None

    #
    # Create new dynamically handled type
    #
    # This function is called at server startup and will create a new type dynamically which
    # can then be handled like any other native Python object
    #
    # @param type_id   Id to identify the trait type, like 'Tom::Token::ObjectFamily'
    # @param type_name Name of the type. The name is used to register the type object at the gom module.
    #                  So the type name 'Vec3d' will lead to the type object 'gom.Vec3d'.
    # @return Created type object
    #

    @staticmethod
    def register_type(type_id, type_name):

        assert type_id not in Types.types, f"'{type_id}' is already registered"

        if type_id in LOCAL_TYPES:
            return None

        params = {'__id__': type_id,
                  '__name__': type_name,
                  '__init__': Types.type_init,
                  '__str__': Types.type_str,
                  '__repr__': Types.type_repr,
                  '__getattr__': Types.type_getattr,
                  '__getattribute__': Types.type_getattribute,
                  '__setattr__': Types.type_setattr,
                  '__getitem__': Types.type_getitem,
                  '__setitem__': Types.type_setitem,
                  '__iter__': Types.type_iter,
                  '__len__': Types.type_len,
                  '__call__': Types.type_call,
                  '__lt__': Types.type_lt,
                  '__le__': Types.type_le,
                  '__eq__': Types.type_eq,
                  '__ne__': Types.type_ne,
                  '__gt__': Types.type_gt,
                  '__ge__': Types.type_ge,
                  '__hash__': Types.type_hash,
                  '__json__': Types.type_json
                  }

        type_obj = type(type_name, (object,), params)
        Types.types[type_id] = type_obj
        Types.type_objs[type_obj] = type_id

        return type_obj

    @staticmethod
    def is_registered_type(type_obj):
        return type_obj in Types.type_objs
