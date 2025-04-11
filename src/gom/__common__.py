#
# common.py - Common classes and functions
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

import re

from enum import Enum
from typing import Any, Callable

# Connection to the ZEISS Inspect application
__connection__ = None


class Constants:
    '''
    Various constants
    '''
    #
    # Names of the wrapper function and wrapper result variable for executing
    # script code as a function
    #
    wrapped_function_name = 'tom_internal_wrapped_script_function'
    wrapped_result_var_name = 'tom_internal_wrapped_script_result'


class Request (Enum):
    '''
    \brief Request id

    This id must match the id in the C++ part
    '''
    API = 1
    COMMAND = 2
    CONFIGURATION = 3
    CONSOLE = 4
    DATA_ARRAY = 5
    DATA_ATTR = 6
    DATA_INDEX = 7
    DATA_SHAPE = 8
    DOC = 9
    EQUAL = 10
    EXCEPTION = 11
    EXIT = 12
    GET = 13
    GETATTR = 14
    FILTER = 15
    IMPORT = 16
    INDEX = 17
    KEY = 18
    LEN = 19
    LESS = 20
    LINE = 21
    LOG = 22
    OBJECTTYPES = 23
    QUERY = 24
    REGISTER = 25
    RELEASE = 26
    REPR = 27
    RESOURCE_KEY = 28
    RESOURCE_LEN = 29
    RESULT = 30
    RUNAPI = 31
    SERVICE = 32
    SETATTR = 33
    SETENV = 34
    TEST = 35
    TOKENS = 36
    TRANSLATE = 37
    TYPE_CALL = 38
    TYPE_CONSTRUCT = 39
    TYPE_CMP = 40
    TYPE_DOC = 41
    TYPE_GETATTR = 42
    TYPE_GETITEM = 43
    TYPE_ITER = 44
    TYPE_LEN = 45
    TYPE_REPR = 46
    TYPE_SETATTR = 47
    TYPE_SETITEM = 48
    TYPE_STR = 49

    TEST_0 = 1000
    TEST_1 = 1001
    TEST_2 = 1002
    TEST_3 = 1003
    TEST_4 = 1004
    TEST_5 = 1005


class Contribution:
    '''
    Base class for all contributions/extensions which can be registered to the application
    '''

    def __init__(self, id: str, category: str, description: str, callables: dict[str, Callable], properties: dict[str, Any]):
        '''
        Constructor

        @param id          Unique contribution id, like 'special_point'
        @param category    Element category, like 'scriptedelement.actual'
        @param description Human readable property name
        @param callables   Dictionary of the callables of the contribution
        @param properties  Dictionary of the property values of the contribution
        '''
        self.id = id
        self.category = category
        self.description = description
        self.callables = callables
        self.properties = properties

        name_pattern = r'^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$'

        if not re.fullmatch(name_pattern, self.id):
            raise RuntimeError(f'Illegal id format {self.id}')

        if not re.fullmatch(name_pattern, self.category):
            raise RuntimeError(f'Illegal category format {self.category}')

        if not self.description.strip():
            raise RuntimeError('Description must not be empty')

    def get_declaration(self):
        return {'id': self.id,
                'category': self.category,
                'description': self.description,
                'callables': self.callables,
                'properties': self.properties}
