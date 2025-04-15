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
@brief Scripted views

The classes in this module enable the user to define scripted views. A scripted view implements a model/view
pair, where a Python script fetches data from the ZEISS INSPECT application (model part) and a JavaScript 
renderer visualizes it in a custom way (view part) inside of a native ZEISS INSPECT view. Also, events can be
emitted from the JavaScript renderer and processed by the Python script.
'''

import gom
import gom.__common__

from abc import ABC
from enum import Enum
from typing import Dict, List, Any, final


class ScriptedView (ABC, gom.__common__.Contribution):
    '''
    @brief This class is the base class for all scripted views

    A scripted view is a view that is embedded into the native ZEISS INSPECT application, but
    its content is rendered by a JavaScript renderer fetching its data from a Python service. Both
    these parts form a model/view pair where the model (the python script) fetches and processes
    the data from the ZEISS INSPECT application, while the view (the JavaScript renderer) visualizes
    it in a custom way.

    The purpose of the `ScriptedView` class now on the one hand is to provide the model, on the other
    hand to bring both parts together.

    **Identification**

    A scripted view is identified by its `id` string. This string must be globally unique, as the scripted
    view code can be part of an app, which shared its id space with other apps installed on the same system.
    It is advised to use a reverse domain name notation for the id, e.g. `com.mycompany.myapp.myview`.

    **Implementation**

    A very simple example for a scripted view API contribution can look like this:

    ```{code-block} python
    :caption: Example of a simple scripted view definition

    import gom
    import gom.api.extensions.views

    from gom import apicontribution

    @apicontribution
    class MyScriptedView (gom.api.extensions.views.ScriptedView):

        def __init__(self):
            super().__init__(id='com.zeiss.testing.scriptedview',
                             description='My Scripted View',
                             renderer='renderers/MyRenderer.js',
                             functions=[
                                 self.get_data
                             ],
                             bundle='npms/MyScriptedView.js')

        def get_data(self):
            return {
                'text': 'Hello World'
            }

    gom.run_api ())    
    ```

    Here, the scripted view

    - has the id `com.zeiss.testing.scriptedview`
    - is named `My Scripted View` in menus etc.
    - exposes the class function `get_data` as a callable function to the JavaScript renderer
    - uses the renderer script `renderers/MyRenderer.js` to visualize the data.

    The JavaScript renderer can call the `get_data` function to get the data to visualize in a custom way
    via the `gom.bridge` object:

    ```{code-block} javascript
    :caption: Accessing data via the scripting bridge from Python

    function renderer () {
        var data = gom.bridge.get_data();
        console.log(data.text);
    }
    ```

    **Event handling**

    The JavaScript renderer can emit events which can then be processed by the python side. There are a few system 
    events, but the renderer itself can produce custom events. The `event` instance method is called by the JavaScript 
    renderer in effect in case of en event. It can be overwritten in custom scripted view implementations:

    ```{code-block} python
    :caption: Example of a scripted view with event handling

    ...
    @apicontribution
    class MyScriptedView (gom.api.extensions.views.ScriptedView):
        ...
        def event(self, event: str, args: Any):
            if event == self.Event.INITIALIZED:
                print('View initialized')
    ```

    On the JavaScript side, the event can be emitted like this:

    ```{code-block} javascript
    :caption: Emitting events from the JavaScript renderer

    function renderer () {
        gom.bridge.__events__.emit('view::initialized', 'Hello World');
    }
    ```

    **Using 3rd party modules**

    ```{caution}
    Please be aware of the necessary FOSS and copyright issues when using 3rd party modules in your apps !
    ```

    JavaScript strongly related to 3rd party modules, for example from node.js. The `bundle` property
    allows to specify a NPM bundle that is used by the JavaScript renderer. The bundle must be present
    as a single file in the `npms` folder of the app. The JavaScript renderer can use this bundle to load 3rd party
    modules. If present, that bundle will be inserted into the JavaScript engine before the renderer process is
    started.

    JavaScript bundles can be creates in various ways, for example via a webpack build. Without going too much into
    detail about the node.js/npm foundations, the following example shows how to create a simple 'react' module bundle
    using node.js and webpack.

    ```{code-block} json
    :caption: Example of a package.json file for bundle creation

        "name": "app-module-bundle",
        "version": 1,
        "description": "App module bundle",
        "private": true,
        "scripts": {
            "build": "webpack --mode production"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-scripts": "^5.0.1"            
        },
        "devDependencies": {
            "webpack": "^5.88.2",
            "webpack-cli": "^5.1.4"
        }
    ```

    Then, a `webpack.config.js` like the following has to be added:

    ```{code-block} javascript
    :caption: Example of a webpack.config.js file for bundle creation

    const path = require('path');

    module.exports = {
        mode: process.env.NODE_ENV || 'production',
        entry: './src/index.js',
        output: {
            path: __dirname + '/dist',
            filename: 'bundle.js',
            library: {
            name: '""" + project_title.replace(' ', '') + """Bundle',
            type: 'umd',
            export: 'default'
            },
            globalObject: 'this'
        },
        // We want to bundle all modules together
        optimization: {
            minimize: true
        }
    };    
    ```

    Please refer to the `node.js` and `webpack` documentation for more details on how to create a bundle. Additionally,
    have a look into the app examples for a more detailed example as a starting point for your own scripted views.
    '''

    class Event(str, Enum):
        '''
        Event types passed to the `event ()` function

        - `INITIALIZED`: Sent when the view has been initialized
        '''
        INITIALIZED = "view::initialized"

    def __init__(self, id: str, description: str, renderer: str, functions: List[Any] = [], properties: Dict[str, Any] = {}, bundle: str = None):
        '''
        Constructor

        @param id          Globally unique scripted view id string
        @param description Human readable name, will appear in menus etc.
        @param renderer    Path to the JavaScript renderer script
        @param functions   List of functions that can be called by the JavaScript renderer
        @param properties  Additional properties
        @param bundle      Packages NPM bundle this scripted view related on
        '''

        if not id:
            raise ValueError('id must be set')
        if not description:
            raise ValueError('description must be set')

        super().__init__(id=id,
                         category='scriptedviews',
                         description=description,
                         callables={
                             'event': self.event
                         },
                         properties={
                             'functions': functions,
                             'renderer': renderer,
                             'bundle': bundle
                         } | properties)

    def event(self, event: str, args: Any):
        '''
        @brief Event handler

        This method is called by the JavaScript renderer when an event is triggered.

        @param event Event name
        @param args  Event arguments
        '''
        pass
