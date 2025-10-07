#
# extensions/views/__init__.py - Scripted views definitions
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
@brief Scripted diagrams

The classes in this module enable the user to define scripted diagrams. A scripted diagram implements an 
interface to transform element data into data that can be rendered by a corresponding Javascript renderer
implementation in the diagram view.
'''

import gom
import gom.__common__

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Tuple, Any, final


class ScriptedDiagram (ABC, gom.__common__.Contribution):
    '''
    This class is used to defined a polisher for a scripted diagram that processes a collection of raw 
    element (diagram) data into a format used by a Javascript based renderer.

    Implement the `plot ()` function to receive and polish diagram data that is marked with the corresponding contribution id.

    Optionally implement the `partitions ()` function to partition the full set of diagram data into subsets 
    that are rendered separately using the `plot ()` function.
    '''
    class Token(str, Enum):
        '''
        Token identifiers for the ScriptedDiagram data format
        '''
        # Plot result
        PLOT = "plot"
        SUBPLOT = "subplot"
        INDICES = "indices"

        # Event result
        CMD_SCRIPT = "cmd_script"
        DATA_SCRIPT = "data_script"

    def __init__(self, id: str, description: str, diagram_type: str = "", properties: Dict[str, Any] = {},
                 callables: Dict[str, Any] = {}):
        '''
        Constructor

        @param id           Unique contribution id, like `my.diagram.circles`
        @param description  Human readable contribution description
        @param diagram_type Javascript renderer to use (leave empty to use renderer set by element)
        @param properties   Additional properties for this contribution (optional)
        @param callables    Addtitional callables for this contribution (optional)
        '''

        if not id:
            raise ValueError('id must be set')
        if not description:
            raise ValueError('description must be set')

        super().__init__(id=id,
                         category='scripteddiagram',
                         description=description,
                         callables={
                             'plot_all': self.plot_all,
                             'event': self.event,
                             'error': self.error
                         } | callables,
                         properties={
                             'diagram_type': diagram_type,
                             # Determine whether the partitions() method has been overwritten
                             'use_partitions': (type(self).partitions != ScriptedDiagram.partitions)
                         } | properties)

    @final
    def check_and_filter_partitions(self, partitions_in: List[List[int]], cnt_elements: int) -> List[List[int]]:
        '''
        Check a given set of partitions to ensure only valid partitions are included.

        @param partitions_in    List of partitions to check
        @param cnt_elements     Count of elements in full data set

        For internal use only.
        '''
        partitions = []
        if isinstance(partitions_in, List):
            for partition in partitions_in:
                if isinstance(partition, List):
                    if all(isinstance(x, int) and x >= 0 and x < cnt_elements for x in partition):
                        partitions.append(partition)
                    else:
                        gom.log.warning(
                            f"Expected only valid integer values [0,{cnt_elements}) in partition, instead got: {partition}")
                else:
                    gom.log.warning(f"Expected a list of indices to define a partition, instead got: {partition}")
        else:
            gom.log.warning(f"Expected a list of partitions, instead got: {partitions_in}")

        return partitions

    @final
    def plot_all(self, view: Dict[str, Any], element_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        '''
        Internal coordination function for the overall plot process.

        This functions calls the (potentially) user defined method 'partitions()' to determine
        the partitions of this diagram and then calls 'plot()' for each to data partition to generate a diagram.

        @param view: Dictionary with view canvas data ('width' (int), 'height' (int), 'dpi' (float), 'font' (int)) used for the diagrams of all partitions
        @param element_data List of dictionaries containing scripted element references and context data ('element' (object), 'data' (dict), 'type' (str))

        @return List of dictionaries: each dictionary contains the keys 'plot' (the plot information for this partition)
                    and 'indices' (the indices of the elements used for this partition)
        '''
        # Fetch partition information and ensure the format is as expected
        partitions = self.check_and_filter_partitions(self.partitions(element_data), len(element_data))

        # If something went terribly wrong, still plot one diagram with all the data
        if len(partitions) == 0:
            view.update({ScriptedDiagram.Token.SUBPLOT: 0})
            return [{ScriptedDiagram.Token.PLOT: self.plot(view, element_data), ScriptedDiagram.Token.INDICES: list(range(len(element_data)))}]

        plots = []
        for num, partition in enumerate(partitions):
            data = []
            indices = set()
            # Collect subset of data
            for idx in partition:
                # Avoid doubled indices
                if idx in indices:
                    continue
                indices.add(idx)
                data.append(element_data[idx])

            # Now plot this subset of data
            view.update({ScriptedDiagram.Token.SUBPLOT: num})
            plots.append({ScriptedDiagram.Token.PLOT: self.sanitize_plot_data(
                self.plot(view, data)), ScriptedDiagram.Token.INDICES: list(indices)})

        return plots

    def sanitize_plot_data(self, plot_data: Any) -> Dict[str, Any]:
        '''
        This function is used to sanitize the output of the user defined 'plot' function
        '''
        return plot_data

    @abstractmethod
    def plot(self, view: Dict[str, Any], element_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        '''
        This function is called to create a plot based on a set of element data. 

        @param view         Dictionary with view canvas data and subplot index ('width' (int), 'height' (int), 'dpi' (float), 'font' (int), 'subplot' (int))
        @param element_data List of dictionaries containing scripted element references and context data ('element' (object), 'data' (dict), 'type' (str))

        @return             Data that is passed to the corresponding Javascript diagram type for rendering
        '''
        pass

    def event(self, element_name: str, element_uuid: str, event_data: Any) -> Dict[str, Any]:
        '''
        This function is called upon interaction with the diagram (except hover)
        The user can return a script to be executed when this function is called

        @param element_name      String containing the element identification (name)
        @param element_uuid      String containing the element uuid for internal identification
        @param event_data        Contains current mouse coordinates and button presses

        @return                  Dictionary with finish_event(<script to be executed>: str, <parameters>: Any)
        '''
        pass

    @final
    def error(self, error_message: str) -> Any:
        gom.log.info(error_message)
        return

    def finish_event(self, cmd_script: str, params=None) -> Dict[str, Any]:
        '''
        This function is called to help return event data in the correct format

        @param cmd_script        Identification of the script command to be executed as a follow-up to this event
        @param params            Optional Parameters to be passed to said script

        @return                  Dictionary with {"cmd_script": cmd_script, "data_script": params}
        '''
        return {ScriptedDiagram.Token.CMD_SCRIPT: cmd_script, ScriptedDiagram.Token.DATA_SCRIPT: params}

    def partitions(self, element_data: List[Dict[str, Any]]) -> List[List[int]]:
        '''
        This function is called to determine the partitions to create multiple plots based on one element data set. 
        Each partition is defined by a list of indices of elements to be used. 
        Each data subset will be passed separately to the plot() function and be rendered as a separate diagram.
        The index of each partition will be available through the 'subplot' key in the view parameters of the plot() function call.

        @param element_data List of dictionaries containing scripted element references and context data ('element' (object), 'data' (dict), 'type' (str))

        @return List of Lists of int: each inner list represents one partition and contains the indices of the elements to be used for that partition

        @info Partitions may share elements
        '''
        return [list(range(len(element_data)))]


class SVGDiagram(ScriptedDiagram):
    '''
    Specialized contribution base for scripted diagrams that are displayed via the SVGDiagram renderer type provided by the Inspect app.

    Provides the helper functions 'finish_plot' and 'add_element_coord' to streamline the creation of the plot data for the SVGRenderer.

    In the most basic form, implement the 'plot' function to return a stringified svg plot. 
    Such data will automatically be sanitized to the full output format.

    For additional interactivity, implement the 'plot' function by returning data using the 'finish_plot(svg_string, overlay)' helper,
    where 'svg_string' is the stringified svg plot 
    and 'overlay' is a point overlay for interaction, that can be created using the 'add_element_coord' helper function.
    '''
    class Token(str, Enum):
        '''
        Token identifiers for the SVGDiagram renderer data format
        '''
        # Rendering related
        SVG_STRING = "svg_string"
        OVERLAY = "overlay"
        RENDER_CONFIG = "render_config"
        DIAGRAM_ID = "diagram_id"

        # Interactivity related
        ELEMENT_NAME = "element_name"
        ELEMENT_UUID = "element_uuid"
        COORDINATES = "coordinates"
        COORD_X = "x"
        COORD_Y = "y"
        TOOLTIP = "tooltip"
        CUSTOM_INTERACTION = "custom_interaction"

        # Auto generated overlay
        TAG_PREFIX = "tag-"
        TAG_SUFFIX = "-tag"

    class RenderConfigToken(str, Enum):
        '''
        Token identifiers for the optional rendering configuration passed to the SVGDiagram renderer via Token.RENDER_CONFIG parameter
        '''

        DEBUG_LOGGING = "debug_logging"
        '''
        Enabled general logging (default: False)
        '''
        DEBUG_LOGGING_TRACE = "debug_logging_trace"
        '''
        Enable detailed result logging (default: False)
        '''
        DEBUG_PERFORMANCE = "debug_performance"
        '''
        Enable performance measuring during the (overlay) rendering process (default: False)
        '''

        DEBUG_ALWAYS_SHOW_OVERLAY = "debug_always_show_overlay"
        '''
        Always show the standard overlay with small black crosses (default: False)
        '''
        DEBUG_AUTO_GENERATED_OVERLAY_SHOW = "debug_auto_generated_overlay_show"
        '''
        Show the hitboxes of the auto generated overlay if available (default: False)
        '''

        DEBUG_NEAREST_POINT_SHOW = "debug_nearest_point_show"
        '''
        Show a small text with the uuid of the nearest element (default: False)
        '''
        DEBUG_NEAREST_POINT_X = "debug_nearest_point_x"
        '''
        X-coordinate of nearest element text if enabled (default: 50)
        '''
        DEBUG_NEAREST_POINT_Y = "debug_nearest_point_y"
        '''
        Y-coordinate of nearest element text if enabled (default: 50)
        '''

        DEBUG_MOUSE_POSITION_SHOW = "debug_mouse_position_show"
        '''
        Show a small text with the mouse coordinates (default: False)
        '''
        DEBUG_MOUSE_POSITION_X = "debug_mouse_position_x"
        '''
        X-coordinate of mouse coordinate text if enabled (default: 50)
        '''
        DEBUG_MOUSE_POSITION_Y = "debug_mouse_position_y"
        '''
        Y-coordinate of mouse coordinate text if enabled (default: 100)
        '''

        NEAREST_MARKER_SHOW = "nearest_marker_show"
        '''
        Show a marker on the element nearest to the mouse (if in event range) (default: True)
        '''
        NEAREST_MARKER_SHAPE = "nearest_marker_shape"
        '''
        Shape of the nearest element marker (default: "cross") (options: "cross", "square", "circle", "dot")
        '''
        NEAREST_MARKER_COLOR = "nearest_marker_color"
        '''
        Color of the nearest element marker (default: <automatic color from diagram view>)
        '''
        NEAREST_MARKER_SIZE = "nearest_marker_size"
        '''
        Size of the nearest element marker (default: 5)
        '''

        DISABLE_TOOLTIPS = "disable_tooltips"
        '''
        Disables all element tooltips of the diagram from being displayed (default: False)
        '''
        DISABLE_MOUSE_EVENTS = "disable_mouse_events"
        '''
        Disables mouse (click) events from being processed (default: False)
        '''

        CUSTOM_HASH = "custom_hash"
        '''
        If defined, use this as a hash for the caching instead of a generated one (default: undefined)
        
        Because matplotlib (and possibly other svg generators) use some unique identifiers and timestamps when generating SVG images, 
        a hash of the resulting SVG varies despite identical input data and settings. 
        Providing a custom hash based on the input data can reduce the amount of rerendering done by the SVGDiagram renderer.
        '''

        AUTO_GENERATED_OVERLAY_USE = "auto_generated_overlay_use"
        '''
        Automatically generate a overlay to determine the hitboxes of elements based on tagged svg groups (default: False)
        '''
        OVERLAY_TAG_PREFIX = "overlay_tag_prefix"
        '''
        Prefix of user defined tags to filter the svg by (default: "tag-" (Token.TAG_PREFIX))
        '''
        OVERLAY_TAG_SUFFIX = "overlay_tag_suffix"
        '''
        Suffix of user defined tags to filter the svg by (default: "-tag" (Token.TAG_SUFFIX))
        '''
        OVERLAY_EXPAND_HITBOXES = "overlay_expand_hitboxes"
        '''
        Expand every hitbox in the auto generated overlay by this number of pixels (default: 10)
        '''
        OVERLAY_USE_MOUSE_POINT = "overlay_use_mouse_position"
        '''
        If TRUE, always use the mouse position instead of a point from the element coords if interacting via the auto generated overlay (default: False)
        '''
        OVERLAY_FILTER_METHOD = "overlay_filter_method"
        '''
        Select the SVG filtering method used to generated the overlay (default: "string-parser") (options: "string-parser", "dom-parser")
        '''
        OVERLAY_ELEMENT_COUNT = "overlay_element_count"
        '''
        Count of elements to be tracked by the overlay. (default: <automatic>)
        Some SVG filtering methods can work more efficient if this given beforehand.
        
        If there are more elements in the plot than this, then not all elements might be added to the overlay correctly.
        '''

    def __init__(self, id: str, description: str, properties: Dict[str, Any] = {},
                 callables: Dict[str, Any] = {}):

        super().__init__(id=id, description=description, diagram_type="SVGDiagram", properties=properties, callables=callables)

    @final
    def sanitize_plot_data(self, plot_data: Any) -> Dict[str, Any]:
        '''
        Sanitize the data returned by the user defined 'plot()' function.

        The SVGDiagram renderer expects a dictionary with fields 'svg_string', 'overlay' and 'diagram_id'.
        '''
        # Raw data received (no dictonary)
        if not type(plot_data) is dict:
            # If the data format is wrong, log some warning, but proceed anyway.
            # The render error will be displayed in the diagram view anyways
            if not type(plot_data) is str:
                gom.log.warning(f"Expected dictionary or string as result from plot, instead got: {type(plot_data)}")
            return self.finish_plot(plot_data)

        # Dictionary received, but main SVG_STRING entry is missing, treat as raw data
        if not SVGDiagram.Token.SVG_STRING in plot_data:
            gom.log.warning(f"Expected dictionary with key '{SVGDiagram.Token.SVG_STRING}' from plot, "
                            f"instead got keys: {plot_data.keys()}")
            return self.finish_plot(plot_data)
        else:
            if not type(plot_data[SVGDiagram.Token.SVG_STRING]) is str:
                gom.log.warning(f"Expected string type in field '{SVGDiagram.Token.SVG_STRING}' as result from plot, "
                                f"instead got: {type(plot_data[SVGDiagram.Token.SVG_STRING])}")

        # Ensure that the OVERLAY key is included
        if not SVGDiagram.Token.OVERLAY in plot_data:
            plot_data[SVGDiagram.Token.OVERLAY] = []

        # Warn if type of OVERLAY field is wrong, proceed anyway
        if not isinstance(plot_data[SVGDiagram.Token.OVERLAY], dict):
            gom.log.warning(f"Expected dictionary type in field '{SVGDiagram.Token.OVERLAY}' as result from plot, "
                            f"instead got: {type(plot_data[SVGDiagram.Token.OVERLAY])}")

        # Warn if diagram id gets replaced
        if SVGDiagram.Token.DIAGRAM_ID in plot_data and plot_data[SVGDiagram.Token.DIAGRAM_ID] != self.id:
            gom.log.warning(
                f"Replacing mismatching contribution id '{plot_data[SVGDiagram.Token.DIAGRAM_ID]} in plot data")

        # Ensure that the DIAGRAM_ID key is included and set to the correct value
        plot_data.update({SVGDiagram.Token.DIAGRAM_ID: self.id})

        return plot_data

    @final
    def finish_plot(self, svg_string: str, overlay: List = [], render_config: Dict = {}) -> Dict[str, Any]:
        '''
        This function is called to help return plot data for the SVGDiagram renderer in the correct format.

        @param svg_string       List of element coordinates that is returned with the added entry
        @param overlay   Point overlay for interaction
        @param render_config    Dictionary with optional render settings

        @return                 Dictionary with svg_string, overlay and diagram_id as keys
        '''
        return {SVGDiagram.Token.SVG_STRING: svg_string,
                SVGDiagram.Token.OVERLAY: overlay,
                SVGDiagram.Token.RENDER_CONFIG: render_config,
                SVGDiagram.Token.DIAGRAM_ID: self.id}

    @final
    def add_element_to_overlay(self, overlay: Dict[str, Dict[str, Any]], element_uuid: Any,
                               interaction_point: Tuple[float, float] = None, element_name: str = "",
                               tooltip=None, custom_interaction=None) -> Dict[str, Dict[str, Any]]:
        '''
        This function is called to add element information to the overlay interaction dictionary.
        Calling the function multiple times for the same element adds the interaction points to a list. 
        Other properties for the element are updated if new valid values are given.

        @param overlay              Dict matching element uuids to the information about that element, that is returned with the added entry
        @param element_name         Optional readable element identification
        @param element_uuid         'uuid' of the element that is being added
        @param tooltip              Optional tooltip to be displayed when hovering the element
        @param interaction_point    Interaction coordinates (x, y) for the element that is being added. 
                                    Should be in relative coordinates to width and height of the plot (see matplotlib_tools -> get_display_coords)
        @param custom_interaction   Flag that, if set to any truthy value, calls the event function when the specific element is interacted with.
                                    Set for the specific interaction point (if given), globally for this element otherwise

        @return                     overlay, dictionary updated with new information for the given element
        '''
        if not element_uuid:
            return overlay

        if element_uuid in overlay:
            if element_name:
                overlay[element_uuid][SVGDiagram.Token.ELEMENT_NAME] = element_name
            if tooltip:
                overlay[element_uuid][SVGDiagram.Token.TOOLTIP] = tooltip
            if not SVGDiagram.Token.COORDINATES in overlay[element_uuid]:
                overlay[element_uuid][SVGDiagram.Token.COORDINATES] = []
        else:
            overlay[element_uuid] = {
                SVGDiagram.Token.ELEMENT_NAME: element_name,
                SVGDiagram.Token.COORDINATES: [],
                SVGDiagram.Token.TOOLTIP: str(tooltip)
            }

        if interaction_point != None:
            overlay[element_uuid][SVGDiagram.Token.COORDINATES].append({
                SVGDiagram.Token.COORD_X: interaction_point[0],
                SVGDiagram.Token.COORD_Y: interaction_point[1],
                SVGDiagram.Token.CUSTOM_INTERACTION: str(custom_interaction)
            })
        else:
            # If no point is specified, store custom interaction parameter as global setting for this element
            if custom_interaction != None:
                overlay[element_uuid][SVGDiagram.Token.CUSTOM_INTERACTION] = custom_interaction

        return overlay

    @final
    def get_overlay_tag(self, element_uuid: str) -> str:
        '''
        Get the tag for the automatic SVG overlay generation based on the element 'uuid'

        @param element_uuid     'uuid' of the element corresponding to the tag
        '''
        return SVGDiagram.Token.TAG_PREFIX + element_uuid + SVGDiagram.Token.TAG_SUFFIX
