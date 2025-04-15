#
# extensions/__init__.py - GOM Extensions API
#
# (C) 2024 Carl Zeiss GOM Metrology GmbH
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
@brief API for script based functionality extensions
 
This API enables the user to define various element classes which can be used to extend the functionality of
ZEISS INSPECT.
'''


import gom.__common__

import gom.api.dialog

from abc import ABC, abstractmethod
from enum import Enum
from typing import final, Dict, Any


class ScriptedElement (ABC, gom.__common__.Contribution):
    '''
    This class is used to define a scripted element. A scripted element is a user defined
    element type where configuration and computation are happening entirely in a Python script,
    so user defined behavior and visualization can be implemented.

    **Element id**

    Every element must have a unique id. It is left to the implementor to avoid inter app conflicts here. The
    id can be hierarchical like `company.topic.group.element_type`. The id may only contain lower case characters, 
    grouping dots and underscores.

    **Element category**

    The category of an element type is used to find the application side counterpart which cares for the
    functionality implementation. For example, `scriptedelement.actual` links that element type the application
    counterpart which cares for scripted actual elements and handles its creation, editing, administration, ...

    **Working with stages**

    Each scripted element must be computed for one or more stages. In the case of a preview or
    for simple project setups, computation is usually done for a single stage only. In case of
    a recalc, computation for many stages is usually required. To support both cases and keep it
    simple for beginners, the scripted elements are using two computation functions:

    - `compute ()`:       Computes the result for one single stage only. If nothing else is implemented,
                          this function will be called for each stage one by one and return the computed
                          value for that stage only. The stage for which the computation is performed is
                          passed via the function's script context, but does usually not matter as all input
                          values are already associated with that single stage.
    - `compute_stages ()`: Computes the results for many (all) stages at once. The value parameters are
                           always vectors of the same size, one entry per stage. This is the case even if
                           there is just one stage in the project. The result is expected to be a result
                           vector of the same size as these stage vectors. The script context passed to that
                           function will contain a list of stages of equal size matching the value's stage
                           ordering.

    So for a project with stages, it is usually sufficient to just implement `compute ()`. For increased
    performance or parallelization, `compute_stages ()` can then be implemented as a second step.

    **Stage indexing**

    Stages are represented by an integer index. No item reference or other resolvable types like
    `gom.script.project[...].stages['Stage #1']` are used because it is assumed that reaching over stage borders into
    other stages' data domain will lead to incorrect or missing dependencies. Instead, if vectorized data or data tensors
    are fetched, the stage sorting within that object will match that stages vector in the context. In the best case, the
    stage vector is just a consecutive range of numbers `(0, 1, 2, 3, ...)` which match the index in a staged tensor.
    Nevertheless, the vector can be number entirely different depending on active/inactive stages, stage sorting, ...

    ```{caution}
    Usually, it is *not* possible to access arbitrary stages of other elements due to recalc restrictions !
    ```
    '''

    class Event(str, Enum):
        '''
        Event types passed to the `event ()` function

        - `DIALOG_INITIALIZE`: Sent when the dialog has been initialized and made visible
        - `DIALOG_CHANGED`:    A dialog widget value changed
        '''
        DIALOG_INITIALIZED = "dialog::initialized"
        DIALOG_CHANGED = "dialog::changed"
        DIALOG_CLOSED = "dialog::closed"

    def __init__(self, id: str, category: str, description: str, element_type: str, callables={}, properties={}):
        '''
        Constructor

        @param id           Unique contribution id, like `special_point`
        @param category     Scripted element type id, like `scriptedelement.actual`
        @param description  Human readable contribution description
        @param element_type Type of the generated element (point, line, ...)
        @param category     Contribution category
        '''

        assert id, "Id must be set"
        assert category, "Category must be set"
        assert description, "Description must be set"
        assert element_type, "Element type must be set"

        super().__init__(id=id,
                         category=category,
                         description=description,
                         callables={
                             'dialog': self.dialog,
                             'event': self.event_handler,
                             'compute': self.compute_stage,
                             'compute_stages': self.compute_stages,
                             'is_visible': self.is_visible
                         } | callables,
                         properties={
                             'element_type': element_type,
                             'icon': bytes()
                         } | properties)

    @abstractmethod
    def dialog(self, context, args):
        '''
        This function is called to create the dialog for the scripted element. The dialog is used to
        configure the element and to provide input values for the computation.

        The dialog arguments are passed as a JSON like map structure. The format is as follows:

        ```
        {
            "version": 1,
            "name": "Element name",
            "values: {
                "widget1": value1,
                "widget2": value2
                ...
            }
        }
        ```

        - `version`: Version of the dialog structure. This is used to allow for future changes in the dialog
                     structure without breaking existing scripts
        - `name`:    Human readable name of the element which is created or edited
        - `values`:  A map of widget names and their initial values. The widget names are the keys and the values
                     are the initial or edited values for the widgets. This map is always present, but can be empty
                     for newly created elements. The element names are matching those in the user defined dialog, so
                     the values can be set accordingly. As a default, use the function `initialize_dialog (args)` to
                     setup all widgets from the args values.

        The helper functions `initialize_dialog ()` and `apply_dialog ()` can be used to initialize the dialog directly.
        and read back the generated values. So a typical dialog function will look like this:

        ```
        def dialog (self, context, args):
            dlg = gom.api.dialog.create ('/dialogs/create_element.gdlg')
            self.initialize_dialog (dlg, args)
            args = self.apply_dialog (args, gom.api.dialog.show (dlg))
            return args
        ```

        For default dialogs, this can be shortened to a call to `show_dialog ()` which will handle the dialog
        creation, initialization and return the dialog values in the correct format in a single call:

        ```
        def dialog (self, context, args):
            return self.show_dialog (context, args, '/dialogs/create_element.gdlg')
        ```

        @param context Script context object containing execution related parameters.
        @param args    Dialog execution arguments. This is a JSON like map structure, see above for the specific format.
        @return Modified arguments. The same `args` object is returned, but must be modified to reflect the actual dialog state.
        '''
        pass

    def show_dialog(self, context, args, url):
        '''
        Show dialog and return the values. This function is a helper function to simplify the dialog creation
        and execution. It will create the dialog, initialize it with the given arguments and show it. The
        resulting values are then returned in the expected return format.

        @param context Script context object containing execution related parameters.
        @param args    Dialog execution arguments. This is a JSON like map structure, see above.
        @param url     Dialog URL of the dialog to show
        '''
        dlg = gom.api.dialog.create(context, url)
        self.initialize_dialog(context, dlg, args)
        return self.apply_dialog(args, gom.api.dialog.show(context, dlg))

    def apply_dialog(self, args, values):
        '''
        Apply dialog values to the dialog arguments. This function is used to read the dialog values
        back into the dialog arguments. See function `dialog ()` for a format description of the arguments.
        '''
        if 'values' not in args:
            args['values'] = {}

        for widget in values:
            args['values'][widget] = values[widget]

        return args

    @final
    def event_handler(self, context, event_type, parameters):
        '''
        Wrapper function for calls to `event ()`. This function is called from the application side
        and will convert the event parameter accordingly
        '''
        return self.event(context, ScriptedElement.Event(event_type), parameters)

    def event(self, context, event_type, parameters):
        '''
        Contribution event handling function. This function is called when the contributions UI state changes.
        The function can then react to that event and update the UI state accordingly. 

        @param context    Script context object containing execution related parameters. This includes the stage this computation call refers to.
        @param event_type Event type
        @param args       Event arguments

        @return `True` if the event requires a recomputation of the elements preview. Upon return, the framework
                will then trigger a call to the `compute ()` function and use its result for a preview update.
                In the case of `False`, no recomputation is triggered and the preview remains unchanged.
        '''

        return event_type == ScriptedElement.Event.DIALOG_INITIALIZED or event_type == ScriptedElement.Event.DIALOG_CHANGED

    @abstractmethod
    def compute(self, context, values):
        '''
        This function is called for a single stage value is to be computed. The input values from the
        associated dialog function are passed as `kwargs` parameters - one value as one specific
        parameter named as the associated input widget.

        @param context Script context object containing execution related parameters. This includes
                       the stage this computation call refers to.
        @param values  Dialog widget values as a dictionary. The keys are the widget names as defined
                       in the dialog definition.
        '''
        pass

    @abstractmethod
    def compute_stage(self, context, values):
        '''
        This function is called for a single stage value is to be computed. The input values from the
        associated dialog function are passed as `kwargs` parameters - one value as one specific
        parameter named as the associated input widget.

        @param context Script context object containing execution related parameters. This includes
                       the stage this computation call refers to.
        @param values  Dialog widget values as a dictionary. The keys are the widget names as defined
                       in the dialog definition.
        '''
        return self.compute(context, values)

    def compute_stages(self, context, values):
        '''
        This function is called to compute multiple stages of the scripted element. The expected result is 
        a vector of the same length as the number of stages.

        The function is calling the `compute ()` function of the scripted element for each stage by default.
        For a more efficient implementation, it can be overwritten and bulk compute many stages at once.

        @param context Script context object containing execution related parameters. This includes
                       the stage this computation call refers to.
        @param values  Dialog widget values as a dictionary.
        '''

        results = []
        states = []

        for stage in context.stages:
            context.stage = stage
            try:
                results.append(self.compute_stage(context, values))
                states.append(True)
            except BaseException as e:
                results.append(str(e))
                states.append(False)

        return {'results': results, 'states': states}

    def is_visible(self, context):
        '''
        This function is called to check if the scripted element is visible in the menus. This is usually the case if
        the selections and other precautions are setup and the user then shall be enabled to create or edit the element.

        The default state is `True`, so this function must be overwritten to add granularity to the elements visibility.

        @return `True` if the element is visible in the menus.
        '''
        return True

    def initialize_dialog(self, context, dlg, args) -> bool:
        '''
        Initializes the dialog from the given arguments. This function is used to setup the dialog
        widgets from the given arguments. The arguments are a map of widget names and their values.

        @param context Script context object containing execution related parameters.
        @param dlg     Dialog handle as created via the `gom.api.dialog.create ()` function
        @param args    Dialog arguments as passed to the `dialog ()` function with the same format as described there. Values which are not found in the dialog are ignored.
        @return `True` if the dialog was successfully initialized and all values could be applied.
                Otherwise, the service's log will show a warning about the missing values.
        '''
        ok = True

        if 'values' in args:
            for widget, value in args['values'].items():
                try:
                    if hasattr(dlg, widget):
                        getattr(dlg, widget).value = value
                except Exception as e:
                    ok = False
                    gom.log.warning(
                        f"Failed to set dialog widget '{widget}' to value '{value}' due to exception: {str(e)}")

        return ok

    def add_target_element_parameter(self, values: Dict[str, Any], element):
        '''
        Adds an element as the target element to the parameters map in the
        appropriate fields

        @param values  Values map
        @param element Element to be added
        '''
        values['target_element'] = element

    def add_selected_element_parameter(self, values: Dict[str, Any]):
        '''
        Adds the current selected element as the target element to the values map

        @param values Values map
        '''
        elements = gom.api.selection.get_selected_elements()
        if len(elements) > 0:
            self.add_target_element_parameter(values, elements[0])

    def check_value(self, values: Dict[str, Any], key: str, value_type: type):
        '''
        Check a single value for expected properties

        @param values:     Dictionary of values
        @param key:        Key of the value to check
        @param value_type: Type the value is expected to have
        '''
        if type(values) != dict:
            raise TypeError(f"Expected a dictionary of values, but got {values}")
        if not key in values:
            raise TypeError(f"Missing '{key}' value")

        v = values[key]
        t = type(v) if type(v) != int else float
        if t != value_type:
            raise TypeError(f"Expected a value of type '{t}' for '{key}', but got '{type(v)}'")

    def check_list(self, values: Dict[str, Any], key: str, value_type: type, length: int):
        '''
        Check tuple result for expected properties

        @param values:     Dictionary of values
        @param key:        Key of the value to check
        @param value_type: Type each of the values is expected to have
        @param length:     Number of values expected in the tuple or 'None' if any length is allowed
        '''
        if not key in values:
            raise TypeError(f"Missing '{key}' value")

        if type(values[key]) != tuple and type(values[key]) != list:
            raise TypeError(f"Expected a tuple or a list type for '{key}'")

        if length and len(values[key]) != length:
            raise TypeError(f"Expected a tuple or a list of {length} values for '{key}'")

        if value_type == float:
            for v in values[key]:
                if type(v) != float and type(v) != int:
                    raise TypeError(f"Expected values of type 'int/float' for '{key}', but got '{type(v)}'")
        elif value_type == gom.Vec3d:
            for v in values[key]:
                if type(v) != gom.Vec3d:
                    if type(v) != list or len(v) != 3:
                        if type(v) != tuple or len(v) != 3:
                            raise TypeError(f"Expected values of type 'Vec3d' for '{key}', but got '{type(v)}'")
        else:
            for v in values[key]:
                if type(v) == value_type:
                    raise TypeError(f"Expected values of type '{value_type}' for '{key}', but got '{type(v)}'")

    def check_target_element(self, values: Dict[str, Any]):
        '''
        Check if a base element (an element the scripted element is constructed upon) is present in the values map
        '''
        self.check_value(values, 'target_element', gom.Item)
