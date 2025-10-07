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
from typing import final, List, Dict, Any

import traceback


class ScriptedElement (ABC, gom.__common__.Contribution):
    '''
    Base class for all scripted elements

    This class is the base class for all scripted element types . A scripted element is a user defined
    element type where configuration and computation are happening entirely in a Python script, so user
    defined behavior and visualization can be implemented.

    **Element id**

    Every element must have a unique id. It is left to the implementer to avoid inter app conflicts here. The
    id can be hierarchical like `company.topic.group.element_type`. The id may only contain lower case characters,
    grouping dots and underscores.

    **Element category**

    The category of an element type is used to find the application side counterpart which cares for the
    functionality implementation. For example, `scriptedelement.actual` links that element type the application
    counterpart which cares for scripted actual elements and handles its creation, editing, administration, ...
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

    class Attribute(str, Enum):
        '''
        Attributes used in the dialog definition

        The attributes are used to define the dialog widgets and their behavior. A selected set of these
        attributes are listed here as a central reference and for unified constant value access.
        '''

        NAME = "name"
        TOLERANCE = "tolerance"
        VALUES = "values"
        VISIBLE = "visible"

    class WidgetType(str, Enum):
        '''
        (Selected) widget types used in the dialog definition

        The widget types are used to define the dialog widgets and their behavior. A selected set of these
        widget types are listed here as a central reference and for unified constant value access.
        '''

        ELEMENTNAME = "input::elementname"
        LABEL = "label"
        LIST = "input::list"
        SEPARATOR = "separator"
        SPACER_HORIZONTAL = "spacer::horizontal"
        SPACER_VERTICAL = "spacer::vertical"
        TOLERANCE = "tolerances"

    def __init__(self, id: str, category: str, description: str, callables={}, properties={}):
        '''
        Constructor

        @param id           Unique contribution id, like `special_point`
        @param category     Scripted element type id, like `scriptedelement.actual`
        @param description  Human readable contribution description
        @param category     Contribution category
        '''

        assert id, "Id must be set"
        assert category, "Category must be set"
        assert description, "Description must be set"

        super().__init__(id=id,
                         category=category,
                         description=description,
                         callables={
                             'add_log_message': self.add_log_message,
                             'apply_dialog': self.apply_dialog,
                             'compute_all': self.compute_all,
                             'dialog': self.dialog,
                             'event': self.event_handler,
                             'finish': self.finish,
                             'is_visible': self.is_visible
                         } | callables,
                         properties={
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
            "name": "Element 1",
            "values: {
                "widget1": value1,
                "widget2": value2
                ...
            }
        }
        ```

        - `version`: Version of the dialog structure. This is used to allow for future changes in the dialog
                     structure without breaking existing scripts
        - `name`:    Human readable name of the element which is created or edited. This entry is inserted automatically
                     from the dialog widget if two conditions are met: The name of the dialog widget is 'name' and its
                     type is 'Element name'. So in principle, the dialog must be setup to contain an 'Element name' widget
                     named 'name' in an appropriate layout location and the rest then happens automatically.
        - `values`:  A map of widget names and their initial values. The widget names are the keys and the values
                     are the initial or edited values for the widgets. This map is always present, but can be empty
                     for newly created elements. The keys are matching the widget names in the user defined dialog, so
                     the values can be set accordingly. As a default, use the function `initialize_dialog (args)` to
                     setup all widgets from the args values.

        The helper functions `initialize_dialog ()` and `apply_dialog ()` can be used to initialize the dialog directly.
        and read back the generated values. So a typical dialog function will look like this:

        ```
        def dialog (self, context, args):
            dlg = gom.api.dialog.create ('/dialogs/create_element.gdlg')
            self.initialize_dialog (dlg, args)
            args = self.apply_dialog (dlg, gom.api.dialog.show (dlg))
            return args
        ```

        The `dlg` object is a handle to the dialog which can be used to access the dialog widgets and their values.
        For example, if a selection element with user defined filter function called `element` is member of the dialog,
        the filter can be applied like this:

        ```
        def dialog (self, context, args):
            dlg = gom.api.dialog.create ('/dialogs/create_element.gdlg')
            dlg.element.filter = self.element_filter
            ...

        def element_filter (self, element):
            return element.type == 'curve'
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

        This function is a shortcut for the following code:

        ```
        dlg = gom.api.dialog.create(context, url)   # Create dialog and return a handle to it
        self.initialize_dialog(context, dlg, args)  # Initialize the dialog with the given arguments
        result = gom.api.dialog.show(context, dlg)  # Show dialog and enter the dialog loop
        return self.apply_dialog(dlg, result)      # Apply the final dialog values
        ```

        @param context Script context object containing execution related parameters.
        @param args    Dialog execution arguments. This is a JSON like map structure, see above.
        @param url     Dialog URL of the dialog to show
        '''
        dlg = gom.api.dialog.create(context, url)
        self.initialize_dialog(context, dlg, args)
        return self.apply_dialog(dlg, gom.api.dialog.show(context, dlg))

    def apply_dialog(self, dlg, result):
        '''
        Apply dialog values to the dialog arguments. This function is used to read the dialog values
        back into the dialog arguments. See function `dialog ()` for a format description of the arguments.

        In its default implementation, the function performs the following tasks:

        - The dialog result contains values for all dialog widgets, including spacers, labels and other displaying only
          widgets. These values are not directly relevant for the dialog arguments and are removed.
        - The name of the created element must be treated in a dedicated way. So the dialog results are scanned for
          an entry named `name` which originates from an element name widget. If this argument is present, it is assumed
          that it configured the dialog name, is removed from the general dialog result and passed as a special `name`
          result instead.
        - The tolerance values are also treated in a dedicated way. If a dialog tolerance widget with the name `tolerance` 
          is present, its value is extracted and included in the final result.

        So the dialog `result` parameters can look like this:

        ```
        {'list': 'one', 'list_label': None, 'threshold': 1.0, 'threshold_label': None, 'name' :'Element 1', 'name_label': None}
        ```

        This will be modified into a format which can be recorded as a script element creation command parameter set:

        ```
        {'name': 'Element 1', 'values': {'list': 'one', 'threshold': 1.0}}
        ```

        This function can be overloaded if necessary and if the parameters must be adapted before being applied:

        ```
        def apply_dialog (self, dlg, result):
            params = super ().apply_dialog (dlg, result)
            # ... Adapt parameters...
            return params
        ```

        For example, if a check should support tolerances, the dialogs tolerance widget value must be present in a parameter called
        'tolerance'. So the `apply_dialog()` function can be tailored like this for that purpose:

        ```
        def apply_dialog (self, dlg, result):
            params = super ().apply_dialog (dlg, result)

            params['name'] = dlg.name.value            # Read result directly from dialog object
            params['tolerance'] = result['tolerance']  # Apply result from dialog result dictionary

            return params
        ```                

        This will result in a dictionary with the parameters which are then used in the elements creation command. When recorded, this could look
        like this:

        ```
        gom.script.scriptedelements.create_actual (name='Element 1', values={'mode': 23, 'threshold': 1.0}, tolerance={'lower': -0.5, 'upper': +0.5})
        ```

        The `values` part will be directly forwarded to the elements custom `compute ()` function, which the `name` and `tolerance` parameters
        are evaluated by the ZEISS INSPECT framework to apply the necessary settings automatically.        

        @param dlg    Dialog handle as created via the `gom.api.dialog.create ()` function
        @param result Dialog result values as returned from the `gom.api.dialog.show ()` function.
        @return Resulting dialog parameters
        '''

        #
        # Extract element name explicitly
        #
        name = None
        if hasattr(dlg, ScriptedElement.Attribute.NAME):
            name_w = getattr(dlg, ScriptedElement.Attribute.NAME)
            if name_w.widget_type == ScriptedElement.WidgetType.ELEMENTNAME:
                name = name_w.value.strip() if name_w.value else '### wrong element name widget type ###'

        #
        # Extract tolerance values explicitly
        #
        tolerance = None

        if hasattr(dlg, ScriptedElement.Attribute.TOLERANCE):
            tolerance_w = getattr(dlg, ScriptedElement.Attribute.TOLERANCE)
            if tolerance_w.widget_type == ScriptedElement.WidgetType.TOLERANCE:
                tolerance = tolerance_w.value

        #
        # Convert the dialog result into a dictionary of values.
        #
        ignore_widget_types = [
            ScriptedElement.WidgetType.LABEL,             # Labels are not values
            ScriptedElement.WidgetType.SEPARATOR,         # Separators are not values
            ScriptedElement.WidgetType.SPACER_HORIZONTAL,  # Spacers are not values
            ScriptedElement.WidgetType.SPACER_VERTICAL    # Spacers are not values
        ]

        values = {}

        for widget in result:
            if hasattr(dlg, widget):
                w = getattr(dlg, widget)
                if w.widget_type == ScriptedElement.WidgetType.LIST:
                    #
                    # Workaround: The list widget is returning the current text which can be translated and is then
                    # different depending on which language is currently set - this is a design flaw. Instead, the
                    # selected index is required. Because the fundamental logic in the script dialog cannot be touched
                    # due to compatibility reasons, the conversation happens here.
                    #
                    values[widget] = w.index
                elif w.name == ScriptedElement.Attribute.NAME and name is not None:
                    pass
                elif w.name == ScriptedElement.Attribute.TOLERANCE and tolerance is not None:
                    pass
                elif w.widget_type in ignore_widget_types:
                    pass
                else:
                    values[widget] = result[widget]

        result = {ScriptedElement.Attribute.VALUES: values}

        if name is None:
            result[ScriptedElement.Attribute.NAME] = '### element name not specified ###'
        else:
            result[ScriptedElement.Attribute.NAME] = name

        if tolerance is not None:
            result[ScriptedElement.Attribute.TOLERANCE] = tolerance

        return result

    @final
    def event_handler(self, context, event_type, parameters):
        '''
        Wrapper function for calls to `event ()`. This function is called from the application side
        and will convert the event parameters accordingly
        '''
        return self.event(context, ScriptedElement.Event(event_type), parameters)

    def event(self, context, event_type, parameters):
        '''
        Contribution event handling function. This function is called when the contributions UI state changes.
        The function can then react to that event and update the UI state accordingly.

        @param context    Script context object containing execution related parameters. This includes the stage this computation call refers to.
        @param event_type Event type
        @param parameters Event arguments

        @return `True` if the event requires a recomputation of the elements preview. Upon return, the framework
                will then trigger a call to the `compute ()` function and use its result for a preview update.
                In the case of `False`, no recomputation is triggered and the preview remains unchanged.
        '''

        return event_type == ScriptedElement.Event.DIALOG_INITIALIZED or event_type == ScriptedElement.Event.DIALOG_CHANGED

    def finish(self, context, results_states_map):
        '''
        This function is called to compile diagram data. It can then later be collected by
        scripted diagrams and displayed. 

        The default option is to simply pass the results and states,
        so this function must be overwritten to utilize other diagrams.

        Example:
        diagram_data = []
        self.add_diagram_data(diagram_data=diagram_data, diagram_id="SVGDiagram",
                              service_id="gom.api.endpoint.example.py", element_data=results_states_map["results"][0])
        results_states_map["diagram_data"] = diagram_data
        @return results_states_map
        '''
        return results_states_map

    def compute_all(self, context, values):
        results_states = self.compute_stages(context, values)
        return self.finish(context, results_states)

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

        if ScriptedElement.Attribute.VALUES in args and args[ScriptedElement.Attribute.VALUES] is not None:
            for widget, value in args[ScriptedElement.Attribute.VALUES].items():
                try:
                    if hasattr(dlg, widget):
                        getattr(dlg, widget).value = value
                except Exception as e:
                    ok = False
                    gom.log.warning(
                        f"Failed to set dialog widget '{widget}' to value '{value}' due to exception: {str(e)}")

        if ScriptedElement.Attribute.NAME in args and args[ScriptedElement.Attribute.NAME]:
            try:
                if hasattr(dlg, ScriptedElement.Attribute.NAME):
                    name_w = getattr(dlg, ScriptedElement.Attribute.NAME)
                    if name_w.widget_type == ScriptedElement.WidgetType.ELEMENTNAME:
                        name_w.value = args[ScriptedElement.Attribute.NAME]
                    else:
                        gom.log.warning(
                            f"Element name parameter given, but dialog widget '{ScriptedElement.Attribute.NAME}' is not of type '{ScriptedElement.WidgetType.ELEMENTNAME}'.")
                else:
                    gom.log.warning(
                        f"Element name parameter given, but dialog does not contain an appropriate widget for element name input.")
            except Exception as e:
                ok = False
                gom.log.warning(
                    f"Failed to set element dialog widget '{ScriptedElement.Attribute.NAME}' to value '{args[ScriptedElement.Attribute.NAME]}' due to exception: {str(e)}")

        if ScriptedElement.Attribute.TOLERANCE in args and args[ScriptedElement.Attribute.TOLERANCE]:
            try:
                if hasattr(dlg, ScriptedElement.Attribute.TOLERANCE):
                    tolerance_w = getattr(dlg, ScriptedElement.Attribute.TOLERANCE)
                    if tolerance_w.widget_type == ScriptedElement.WidgetType.TOLERANCE:
                        tolerance_w.value = args[ScriptedElement.Attribute.TOLERANCE]
                    else:
                        gom.log.warning(
                            f"Element tolerance parameter given, but dialog widget '{ScriptedElement.Attribute.TOLERANCE}' is not of type '{ScriptedElement.WidgetType.TOLERANCE}'.")
                else:
                    gom.log.warning(
                        f"Element tolerance parameter given, but dialog does not contain an appropriate widget for element tolerance input.")
            except Exception as e:
                ok = False
                gom.log.warning(
                    f"Failed to set element dialog widget '{ScriptedElement.Attribute.TOLERANCE}' to value '{args[ScriptedElement.Attribute.TOLERANCE]}' due to exception: {str(e)}")

        return ok

    def add_diagram_data(self, diagram_data: List, diagram_id: str, service_id: str, element_data: Dict[str, Any]):
        diagram_data.append({
            "element_id": self.id,
            "diagram_id": diagram_id,
            "service_id": service_id,
            "element_data": element_data
        })

    def add_log_message(self, context, level, message):
        '''
        Add a log message to the service log. The message will be logged with the given level and appear
        in the service log file. It is used to forward errors from the C++ side to the Python side.

        @param context Script context object containing execution related parameters.
        @param level   Log level
        @param message Log message to be added
        '''
        if level.lower() == 'error':
            gom.log.error(message)
        elif level.lower() == 'warn':
            gom.log.warning(message)
        elif level.lower() == 'info':
            gom.log.info(message)
        elif level.lower() == 'fatal':
            gom.log.critical(message)
        elif level.lower() == 'debug':
            gom.log.debug(message)
        else:
            gom.log.info(message)

    def check_value(self, values: Dict[str, Any], key: str, value_type: type):
        '''
        Check a single value for expected properties

        @param values     Dictionary of values
        @param key        Key of the value to check
        @param value_type Type the value is expected to have
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

        @param values     Dictionary of values
        @param key        Key of the value to check
        @param value_type Type each of the values is expected to have
        @param length     Number of values expected in the tuple or 'None' if any length is allowed
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


class ScriptedCalculationElement (ScriptedElement):
    '''
    This class is used to define a scripted calculation element which calculated its own data. It is used as a
    base class for scripted actual, nominals and checks.

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

    def __init__(self, id: str, category: str, description: str, element_type: str, callables={}, properties={}):
        '''
        Constructor

        @param id           Unique contribution id, like `special_point`
        @param category     Scripted element type id, like `scriptedelement.actual`
        @param description  Human readable contribution description
        @param element_type Type of the generated element (point, line, ...)
        @param category     Contribution category
        '''

        assert element_type, "Element type must be set"

        super().__init__(id=id,
                         category=category,
                         description=description,
                         callables={
                             'compute': self.compute_stage,
                             'compute_stages': self.compute_stages,
                         } | callables,
                         properties={
                             'element_type': element_type
                         } | properties)

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

        #
        # Iterate over the stage indices. Each stage is computed separately per default.
        # If set, the `context.stage` property determines from which stage the tokens etc.
        # are queried.
        #
        for stage in context.stages:
            context.stage = stage
            try:
                results.append(self.compute_stage(context, values))
                states.append(True)
            except BaseException as e:
                results.append((str(e), traceback.format_exc()))
                states.append(False)
            finally:
                context.stage = None

        return {'results': results, 'states': states}
