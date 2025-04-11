#
# extensions/inspections/__init__.py - Scripted element inspection definitions
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

from gom.api.extensions import ScriptedElement
from typing import Dict, Any

import gom.api.scriptedelements
import gom.api.selection


class ScriptedInspection (ScriptedElement):
    '''
    This class is the base class for all scripted inspections
    '''

    def __init__(self, id: str, description: str, element_type: str, typename: str, unit: str, abbreviation: str, help_id: str):
        '''
        Constructor

        @param id            Scripted actual id string
        @param description   Human readable name, will appear in menus
        @param element_type  Type of the generated element (inspection.scalar, inspection.surface, ...)
        @param type_name     Scripted inspection type name. Must be a globally unique name.
        @param unit          Unit of the inspection value
        @param abbreviation  Abbreviation of the inspection type
        '''

        assert typename, "Inspection type name must be set"
        assert unit, "Unit must be set"
        assert abbreviation, "Abbreviation must be set"
        assert not gom.api.scriptedelements.get_inspection_definition(
            typename), f"Inspection type name '{typename}' is already in use"
        assert gom.api.scriptedelements.get_unit_definition(unit), f"'{unit}' is not a valid unit"

        properties = {
            'typename': typename,
            'unit': unit,
            'abbreviation': abbreviation
        }

        if help_id:
            properties['help_id'] = help_id

        super().__init__(id=id, category='scriptedelement.inspection', description=description, element_type=element_type,
                         properties=properties)


class Scalar (ScriptedInspection):
    '''
    Scripted scalar inspection

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "nominal": float,           // Nominal value
        "actual": float,            // Actual value
        "target_element": gom.Item  // Inspected element
    }
    ```
    '''

    def __init__(self, id: str, description: str, typename: str, unit: str, abbreviation: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='inspection.scalar',
                         typename=typename, unit=unit, abbreviation=abbreviation, help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.add_selected_element_parameter(result)

        self.check_target_element(result)
        self.check_value(result, 'nominal', float)
        self.check_value(result, 'actual', float)

        return result


class Surface (ScriptedInspection):
    '''
    Scripted surface inspection

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "deviation_values": [v: float, v: float, ...] // Deviations
        "nominal": float,                             // Nominal value
        "target_element": gom.Item                    // Inspected element
    }
    ```
    '''

    def __init__(self, id: str, description: str, typename: str, unit: str, abbreviation: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='inspection.surface',
                         typename=typename, unit=unit, abbreviation=abbreviation, help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.add_selected_element_parameter(result)

        self.check_target_element(result)
        self.check_list(result, 'deviation_values', float, None)
        self.check_value(result, 'nominal', float)

        return result


class Curve (ScriptedInspection):
    '''
    Scripted curve inspection

    The expected parameters from the elements `compute ()` function is a map with the following format:

    ```
    {
        "actual_values": [v: float, v: float, ...] // Deviations
        "nominal": float,                          // Nominal value
        "target_element": gom.Item                 // Inspected element
    }
    ```
    '''

    def __init__(self, id: str, description: str, typename: str, unit: str, abbreviation: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='inspection.curve',
                         typename=typename, unit=unit, abbreviation=abbreviation, help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.add_selected_element_parameter(result)

        self.check_target_element(result)
        self.check_list(result, 'actual_values', float, None)
        self.check_value(result, 'nominal', float)

        return result
