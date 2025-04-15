#
# extensions/nominals/__init__.py - Scripted element nominal definitions
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


class ScriptedNominal (ScriptedElement):
    '''
    This class is the base class for all scripted nominals
    '''

    def __init__(self, id: str, description: str, element_type: str, help_id: str):
        '''
        Constructor

        @param id           Scripted nominal id string
        @param description  Human readable name, will appear in menus
        @param element_type Type of the generated element (point, line, ...)
        '''
        properties = {}
        if help_id:
            properties['help_id'] = help_id

        super().__init__(id=id, category='scriptedelement.nominal',
                         description=description, element_type=element_type, properties=properties)


class Point (ScriptedNominal):
    '''
    Scripted nominal point element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "value": (x: float, y: float, z: float) // The point in 3D space.
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='point', help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.check_list(result, "value", float, 3)

        return result


class Distance (ScriptedNominal):
    '''
    Scripted nominal distance element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "point1": (x: float, y: float, z: float), // First point of the distance
        "point2": (x: float, y: float, z: float)  // Second point of the distance
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='distance', help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.check_list(result, "point1", float, 3)
        self.check_list(result, "point2", float, 3)

        return result


class Circle (ScriptedNominal):
    '''
    Scripted nominal circle element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "center"   : (x: float, y: float, z: float), // Centerpoint of the circle
        "direction": (x: float, y: float, z: float), // Direction/normal of the circle
        "radius"   : r: float                        // Radius of the circle
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='circle', help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.check_list(result, "center", float, 3)
        self.check_list(result, "direction", float, 3)
        self.check_value(result, "radius", float)

        return result


class Cone (ScriptedNominal):
    '''
    Scripted nominal cone element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "point1": (x: float, y: float, z: float), // First point of the cone (circle center)
        "radius1": r1: float,                     // Radius of the first circle
        "point2": (x: float, y: float, z: float), // Second point of the cone (circle center)
        "radius2": r2: float                      // Radius of the second circle
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='cone', help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.check_list(result, "point1", float, 3)
        self.check_value(result, "radius1", float)
        self.check_list(result, "point2", float, 3)
        self.check_value(result, "radius2", float)

        return result


class Cylinder (ScriptedNominal):
    '''
    Scripted nominal cylinder element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "point": (x: float, y: float, z: float),     // Base point of the cylinder
        "direction": (x: float, y: float, z: float), // Direction of the cylinder
        "radius": r: float,                          // Radius of the cylinder
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='cylinder', help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.check_list(result, "point", float, 3)
        self.check_list(result, "direction", float, 3)
        self.check_value(result, "radius", float)

        return result


class Plane (ScriptedNominal):
    '''
    Scripted nominal plane element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "normal": (x: float, y: float, z: float), // Normal of the plane
        "distance": d: float                      // Distance of the plane
    }
    ```

    or 

    ```
    {
        "target": plane: Plane, // Source plane point of this plane
        "offset": offset: float // Offset relative to the source place
    }
    ```

    or

    ```
    {
        "plane": Reference // Reference to another plane element of coordinate system
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='plane', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class ValueElement (ScriptedNominal):
    '''
    Scripted nominal value element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "value": v: float // Value of the element
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='value_element', help_id=help_id)

    def compute_stage(self, context, values):
        result = self.compute(context, values)

        self.check_value_type(values, "value", float)

        return result


class Curve (ScriptedNominal):
    '''
    Scripted nominal curve element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "plane": p: Plane // Plane of the curve (optional)
        "curves": [Curve] // List of curves
    }
    ```

    The format of the `Curve` object is:

    ```
    {
        "points": [(x: float, y: float, z: float), ...] // List of points
    }
    ```

    See the `Plane` element for the formats of the plane object.
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='curve', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class SurfaceCurve (ScriptedNominal):
    '''
    Scripted nominal surface curve element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "curves": [Curve]
    }
    ```

    The format of the `Curve` object is:

    ```
    {
        "points":  [(x: float, y: float, z: float), ...] // List of points
        "normals": [(x: float, y: float, z: float), ...] // List of normals for each point
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='surface_curve', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class Section (ScriptedNominal):
    '''
    Scripted nominal section element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "curves": [Curve],
        "plane": Plane,
        "cone": Cone,
        "cylinder": Cylinder
    }
    ```

    The format of the `Curve` object is:

    ```
    {
        "points":  [(x: float, y: float, z: float), ...] // List of points
        "normals": [(x: float, y: float, z: float), ...] // List of normals for each point
    }
    ```

    See the `Plane`, `Cone` and `Cylinder` element for the formats of the plane, cone and cylinder object.
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='section', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class PointCloud (ScriptedNominal):
    '''
    Scripted nominal point cloud element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "points":  [(x: float, y: float, z: float), ...], // List of points
        "normals": [(x: float, y: float, z: float), ...]  // List of normals for each point
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='point_cloud', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class Surface (ScriptedNominal):
    '''
    Scripted nominal surface element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "vertices":  [(x: float, y: float, z: float), ...], // List of vertices
        "triangles": [(i1: int, i2: int, i3: int), ...]     // List of triangles (vertices indices)
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='surface', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)
