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
combines a sequence of commands into one sequence. The sequence is treated as one single combined element
with parts. The resulting cluster of elements can then be edited again as a altogether sequence, of the
single elements within can be edited separately.
'''

import gom
from gom.api.extensions import ScriptedElement

from abc import abstractmethod


class ScriptedSequence (ScriptedElement):
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
                         callables={'create': self.create,
                                    'edit': self.edit})

    @abstractmethod
    def create(self, context, name, args):
        '''
        Function called to create a sequence of elements

        **Sequence creation**

        This function is called to create a sequence of elements initially. It can use the regular scripted
        creation commands to create the elements of that sequence and determine which of these elements is
        the 'leading' element of the sequence. The leading element is the one which represents the whole
        sequence in the sense that editing the sequence again is initialzed by editing the leading element or
        deleting the leading element deletes the whole sequence.

        Example:

        ```
        def create (self, context, name, args):

          #
          # Extract parameters from the dialog
          #
          distance = args['distance']

          #
          # Create sequence via the regular creation commands. Here, two points and a distance
          # between these points is created, with the distance being the leading element.
          #
          POINT_1=gom.script.primitive.create_point (
            name=self.generate_element_name (name, 'First point'), 
            point={'point': gom.Vec3d (0.0, 0.0, 0.0)})

          POINT_2=gom.script.primitive.create_point (
            name=self.generate_element_name (name, 'Second point'), 
            point={'point': gom.Vec3d (distance, 0.0, 0.0)})

          DISTANCE=gom.script.inspection.create_distance_by_2_points (
            name = name,
            point1=POINT_1, 
            point2=POINT_2)

          #
          # Return created sequence elements and the leading element of that sequence
          #
          return {'elements': [POINT_1, POINT_2, DISTANCE], 'leading': DISTANCE}  
        ```

        **Element naming**

        Element names must be unique within a project. Also, the elements belonging to the same sequence should be 
        identifiable via their names. To assure this, the element names should be computed via the API function 
        `generate_element_name()`. Please see documentation of this function for details.

        @param context  The context of the element
        @param name     Name of the leading element, extracted from the dialog.
        @param args     The arguments passed to the sequence, usually from the configuration dialog
        @return Dictionary describing the created element. The fields here are:
                `elements` - List of all created elements (including the leading element)
                `leading` - 'Leading' element which represents the whole sequence
        '''
        pass

    @abstractmethod
    def edit(self, context, elements, args):
        '''
        Function called to edit the scripted sequence

        This function is called when a scripted sequence is edited. It will receive the current sequence elements
        together with the current sequence creation dialog values and must reconfigure the sequence elements accordingly.

        Example:

        ```
        def edit (self, context, elements, args):

          #
          # The 'elements' parameter is a list containing the elements in the
          # same order as returned by the 'create()' function
          #
          POINT_1, POINT_2, DISTANCE = elements

          #
          # Actual dialog parameters
          #
          distance = args['distance']

          gom.script.sys.edit_creation_parameters (
            element=POINT_2, 
            point={'point': gom.Vec3d (distance, 0.0, 0.0)})        
        ```

        @param context  The context of the sequence
        @param elements List of current elements of the sequence in the same order as returned by the `create()` function
        @param args     Creation arguments from the dialog
        '''
        pass

    def generate_element_name(self, leading_name, basename):
        '''
        Generates a unique name for an element of the scripted sequence.

        This function generates a unique name for an element of the scripted sequence. The name is based 
        on the leading element of the sequence, plus a base name and a running number.

        **Example**

        For a sequence with id `Distance 1` and a base name `Point`, the generated names will be
        `Distance 1 ● Point 1`, `Distance 1 ● Point 2`, ...

        When implemented, the `create()` function of the scripted sequence should use this function
        to generate the names of the single elements:

        ```python
        def create(self, context, name, args):

            distance = args['distance']  # Distance from dialog

            POINT_1 = gom.script.primitive.create_point(
                name=self.generate_element_name(name, 'First point'),
                point={'point': gom.Vec3d(0.0, 0.0, 0.0)})

            POINT_2 = gom.script.primitive.create_point(
                name=self.generate_element_name(name, 'Second point'),
                point={'point': gom.Vec3d(distance, 0.0, 0.0)})

            DISTANCE = gom.script.inspection.create_distance_by_2_points(
                name=name,
                point1=POINT_1,
                point2=POINT_2)

            return {'elements': [POINT_1, POINT_2, DISTANCE], 'leading': DISTANCE}
        ```
        @param leading_name Name of the leading element of the sequence. This is usually the name as
                            specified in the creation dialog.
        @param basename     Base name for the element, like `Point` or `Line`. This name part will be
                            extended by a running number to make it unique.
        @return Generated unique name
        '''
        return f'{leading_name} ● {basename}'
