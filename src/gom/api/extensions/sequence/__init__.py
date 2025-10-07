#
# extensions/sequence/__init__.py - Scripted sequence elements
#
# (C) 2025 Carl Zeiss GOM Metrology GmbH
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
'''
@brief Scripted sequence elements
 
This module contains the base class for scripted sequence elements. A scripted sequence element
combines a sequence of commands into one group. The group is treated as one single combined element
with parts. The resulting cluster of elements can then be edited again as a altogether group, of the
single elements within can be edited separately.
'''

import gom
from gom.api.extensions import ScriptedElement

from abc import abstractmethod


class ScriptedSequenceElement (ScriptedElement):
    '''
    This class is used to define a scripted sequence element
    '''

    def __init__(self, id: str, description: str):
        '''
        Constructor

        @param id           Unique contribution id, like `special_point`
        @param description  Human readable contribution description
        '''

        assert id, "Id must be set"
        assert description, "Description must be set"

        super().__init__(id=id,
                         category='scriptedelement.sequence',
                         description=description,
                         callables={'create': self.create})

    @abstractmethod
    def create(self, context, args):
        '''
        Function called to create the scripted sequence

        This function is called to create or edit the element of a scripted sequence. The
        parameters set in the `dialog` function are passed here as a parameter.

        In principle, this function is like a sub script calling the single create commands.
        Behind the scenes, the calls are handled a bit different than regular script command 
        calls to be able to build a component object at the end. In detail, the following rules
        apply:

        - The order of elements must remain the same during object lifetime. So no parameter or
          external condition may change the element order.
        - The number of elements must remain the same during object lifetime. No parameter or
          condition may affect the number of created elements.
        - There may not be other glue code commands in the sequence. Only creation commands are allowed
          here. In principle, other glue code is allowed, including API calls.

        These limitations are required because behind the scenes, the scripting engine processes the
        creation requests depending on the mode of sequence command execution:

        - For a simple creation process (like a scripted sequence creation command), the command list is
          executed like any other script.
        - When an existing creation sequence is edited, the command list is **not** executed regularly.
          Instead, the command parameters are collected and will be passed to the already existing 
          elements to adapt these.
        - For preview computation, a combination of both modes is used: The objects are created in a first
          step, but marked as 'preview' and will not be part of the regular dependency graph or project.
          Afterwards, like in the 'edit' case, the parameters are collected and passed to the already 
          existing preview elements then to update these. 

        @param context  The context of the sequence element
        @param args     The arguments passed to the sequence element, usually from the configuration dialog
        @return Dictionary describing the created sequence element. The fields here are:
                'elements' - List of all created elements (including the leading element)
                'leading' - 'Leading' element which represents the whole sequence
        '''
        pass
