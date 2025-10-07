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

from gom.api.extensions import ScriptedCalculationElement
import gom.api.scriptedelements


class ScriptedInspection (ScriptedCalculationElement):
    '''
    This class is the base class for all scripted inspections

    Scripted inspections are used to inspect elements in the 3D view, like scalar, surface or curve inspections.
    There are specialized classes for each inspection type, like `Scalar`, `Surface` or `Curve`, which inherit from this
    class. The `ScriptedInspection` class is used to define the common properties of all scripted inspections.

    **The target element**

    The `self.compute ()` function of every scripted inspection expects a `target_element` value which is the element
    which is inspected by the check. This inspected element is usually queried in the checks dialog, but can also be
    or depend on the currently selected element in the 3D view. So the return parameter of the `self.compute ()`
    function looks like this:

    ```
    {
        "target_element": my_dialog.element_selector.value, # The inspected element as selected in a dialog widget
        "data": {...}                                       # Optional data, stored with the element
        ...                                                 # Specific data required by the inspection type
    }
    ```

    To avoid background magic, the `target_element` must be explicitly returned by the `self.compute ()` function and
    there is no automatic insertion of a possibly selected element. So if the check should inspect the currently
    selected element in the 3D view, this must be coded explicitly in the `self.compute ()` function:

    ```
    import gom.api.selection

    def compute (self, context, values):
        selected = gom.api.selection.get_selected_elements()
        if len (selected) != 1:
            raise ValueError("Please select exactly one element to inspect")

        return {
            "target_element": selected[0],
            "data": {},                                      # Optional data, stored with the element
            ...                                              # Specific data required by the check type
        }
    ```

    '''

    def __init__(self, id: str, description: str, element_type: str, dimension: str, abbreviation: str, help_id: str):
        '''
        Constructor

        **Units and dimensions**

        In principle, the term

        * 'dimension' refers to a physical dimension which is measured, like 'length', 'time', 'angle', 'force', 'pressure', etc. while
        * 'unit' refers to a specific unit to quantify that dimension, like the units 'inch', 'mm', 'm', ... for the dimension 'length'.

        These two terms are often mixed up, but dimension describes the type of physical quantity, while unit describes the scale or standard
        used to measure it. When using scripts checks, it is important to understand that

        * the 'dimension' of an element must be set explicitly in the script while
        * all internal calculations are done in the *base unit* of that dimension (which is 'mm' for 'length', 's' for 'time', etc.) and
        * a setting in the ZEISS INSPECT preferences defines the *displayed unit* for that dimension, like 'inch' or 'mm' for 'length'.

        So, for example, if a scripted check is computing a value with the dimension 'angle', the base unit of that dimension is always
        'radian'. The expected values will be in the range [0, 2*pi] and the displayed unit will be transformed to the
        currently set unit in the preferences. The displayed unit is usually 'degree', so the computed value is transformed internally
        in the applications labels, tables, reports etc. to the range [0, 360] and displayed as such.

        The ids for the available dimensions can very over time and are hardcoded in the ZEISS INSPECT application. It is avised to
        use the `gom.api.scriptedelements.get_dimensions ()` function to get a list of all available dimensions in the current version of the
        application and choose one of the returned ids as the `dimension` parameter in the constructor instead of relying to static
        dimension id lists:

        ```
        import gom.api.scriptedelements

        for id in gom.api.scriptedelements.get_dimensions():
            info = gom.api.scriptedelements.get_dimension_definition(id)
            print(f"Dimension id: {id}, name: {info['name']}, units: {info['units']}, default: {info['default']}")
        ```

        **Abbreviation**

        The `abbreviation` parameter is a short string which is used to identify the inspection type in labels, menus, etc.

        **Tolerances**

        Inspections are supporting tolerances. A tolerance is a limit which defines the inspected value quality and is defined 
        right at the inspection element. For this, a special element dialog widget 'tolerance' is defined which returns a
        representation of the tolerance limits. When used, this widgets value must be forwarded via a special return value
        named 'tolerance'. This can best be done in a customized `apply_dialog()` function which is called to generate the 
        `dialog ()` function return dictionary from the dialogs result:

        ```
        def apply_dialog (self, dlg, result):
            params = super ().apply_dialog (dlg, result)

            params['name'] = result['name']           # Dialog widget named 'name' sets the element name
            params['tolerance'] = result['tolerance'] # Dialog widget named 'tolerance' sets tolerance values

            #
            # So the resulting dictionary is of the following format:
            #
            # {'name': 'Element 1', 'tolerance': {'lower': 0.1, 'upper': 0.2}, 'values': {'threshold': 0.5, 'mode:' 23}}
            #
            # This will lead to three parameters in the recorded check creating command with specific semantics.
            #

            return params
        ```

        @param id           Scripted inspection id string
        @param description  Human readable name, will appear in menus
        @param element_type Type of the generated element (inspection.scalar, inspection.surface, ...)
        @param dimension    Dimension of the inspection value. See above for detailed explanation.
        @param abbreviation Abbreviation of the inspection type as shown in labels etc.
        '''

        dimensions = ','.join(gom.api.scriptedelements.get_dimensions())

        assert id, "Inspection id name must be set"
        assert dimension, f"Dimension must be set. Valid dimensions are: {dimensions}"
        assert abbreviation, "Abbreviation must be set"
        assert gom.api.scriptedelements.get_dimension_definition(
            dimension), f"'{dimension}' is not a valid dimension. Valid dimensions are: {dimensions}"

        properties = {
            'typename': id,
            'unit': dimension,
            'abbreviation': abbreviation
        }

        if help_id:
            properties['help_id'] = help_id

        super().__init__(id=id, category='scriptedelement.inspection', description=description, element_type=element_type,
                         properties=properties)


class Scalar (ScriptedInspection):
    '''
    Scripted scalar inspection

    Please see the base class `ScriptedInspection` for a discussion of the properties all scripted inspection types
    have in common.

    **Return value**

    The expected parameters from the element's `self.compute ()` function is a map with the following format:

    ```
    {
        "nominal": float,           // Nominal value
        "actual": float,            // Actual value
        "target_element": gom.Item, // Inspected element
        "data": {...}               // Optional element data, stored with the element
    }
    ```
    '''

    def __init__(self, id: str, description: str, dimension: str, abbreviation: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='inspection.scalar',
                         dimension=dimension, abbreviation=abbreviation, help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.check_target_element(result)
        self.check_value(result, 'nominal', float)
        self.check_value(result, 'actual', float)

        return result


class Surface (ScriptedInspection):
    '''
    Scripted surface inspection

    Please see the base class `ScriptedInspection` for a discussion of the properties all scripted inspection types
    have in common.

    **Return value**

    The expected parameters from the element's `self.compute ()` function is a map with the following format:

    ```
    {
        "deviation_values": [v: float, v: float, ...] // Deviations
        "nominal": float,                             // Nominal value
        "target_element": gom.Item,                   // Inspected element
        "data": {...}                                 // Optional element data, stored with the element
    }
    ```
    '''

    def __init__(self, id: str, description: str, dimension: str, abbreviation: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='inspection.surface',
                         dimension=dimension, abbreviation=abbreviation, help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.check_target_element(result)
        self.check_list(result, 'deviation_values', float, None)
        self.check_value(result, 'nominal', float)

        return result


class Curve (ScriptedInspection):
    '''
    Scripted curve inspection

    Please see the base class `ScriptedInspection` for a discussion of the properties all scripted inspection types
    have in common.

    **Return value**

    The expected parameters from the elements `self.compute ()` function is a map with the following format:

    ```
    {
        "actual_values": [float, ...]  // Deviations
        "nominal_values": [float, ...] // Nominal values

         ...or alternatively...

        "nominal_value": float,        // Alternative: Single common nominal value
        "target_element": gom.Item,    // Inspected element
        "data": {...}                  // Optional element data, stored with the element
    }
    ```
    '''

    def __init__(self, id: str, description: str, dimension: str, abbreviation: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='inspection.curve',
                         dimension=dimension, abbreviation=abbreviation, help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.check_target_element(result)
        self.check_list(result, 'actual_values', float, None)

        try:
            self.check_value(result, 'nominal_value', float)
        except TypeError:
            self.check_list(result, 'nominal_values', float, None)

        return result
