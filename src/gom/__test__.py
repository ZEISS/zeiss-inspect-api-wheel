#
# test.py - Classes and functions for testing the Python functionality.
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


class TestInterface:
    '''
    \brief Function collection for debugging and testing
    '''

    def reflect(self, value):
        '''
        Send the given value over the interface to the server and receives the same value afterwards 
        again the same way. 

        This function can be used to test test communication protocol,

        @param value Value to be reflected
        @return The reflected value
        '''
        return gom.__common__.__connection__.request(Request.TEST,
                                                     {'command': 'reflect', 'data': value})

    def crash(self, method):
        '''
        Trigger a server crash

        This function can be used to trigger a crash of the server to test crashing behaviour 
        (exception handling, client termination, ...)

        @param method Kind of crash to perform. Can be either 'access' for a memory access error and
                                  'progerror' for a raised ProgError exception. 
        '''
        return gom.__common__.__connection__.request(Request.TEST,
                                                     {'command': 'crash', 'method': method})

    def query(self, elements, expressions, mode='token'):
        '''
        Send a bulk of expressions to be evaluated to the server and receive a matching bulk reply.

        This function is used to query a set of tokens or expressions of an element at once, without
        needing to send each single request over the interface. It is used to speed up test scripts
        where lots of tokens have to be tested and which would otherwise be very slow.

        @param elements	   List of elements from which the expressions should be queried.
        @param expressions List of expressions to query.
        @param mode		   Query mode. Can be either 'token' for direct token interface queries or
                                           'expression' for queries via the expression cache.
        @return	List of result, one result list per queried element. The result lists are matching the
                expression list in means of order. 
        '''
        return gom.__common__.__connection__.request(Request.QUERY,
                                                     {'elements': elements, 'expressions': expressions, 'mode': mode})
