#
# extensions/actuals/__init__.py - Scripted element actual definitions
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
@brief Scripted actual elements
 
The classes in this module are used to define scripted actual elements. These elements are used to generate
actuals in the ZEISS INSPECT software and will enable the user to create script defined element types.
'''

import gom

from gom.api.extensions import ScriptedElement


class ScriptedActual (ScriptedElement):
    '''
    This class is the base class for all scripted actuals
    '''

    def __init__(self, id: str, description: str, element_type: str, help_id: str):
        '''
        Constructor

        @param id           Scripted actual id string
        @param description  Human readable name, will appear in menus
        @param element_type Type of the generated element (point, line, ...)
        '''
        properties = {}
        if help_id:
            properties['help_id'] = help_id

        super().__init__(id=id, category='scriptedelement.actual',
                         description=description, element_type=element_type, properties=properties)


class Point (ScriptedActual):
    '''
    Scripted actual point element

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


class Distance (ScriptedActual):
    '''
    Scripted actual distance element

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


class Circle (ScriptedActual):
    '''
    Scripted actual circle element

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


class Cone (ScriptedActual):
    '''
    Scripted actual cone element

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


class Cylinder (ScriptedActual):
    '''
    Scripted actual cylinder element

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


class Plane (ScriptedActual):
    '''
    Scripted actual plane element

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
        "offset": offset: float // Offset relative to the source plane
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


class ValueElement (ScriptedActual):
    '''
    Scripted actual value element

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

        self.check_value(result, "value", float)

        return result


class Curve (ScriptedActual):
    '''
    Scripted actual curve element

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


class SurfaceCurve (ScriptedActual):
    '''
    Scripted actual surface curve element

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


class Section (ScriptedActual):
    '''
    Scripted actual section element

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


class PointCloud (ScriptedActual):
    '''
    Scripted actual point cloud element

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

        result = self.compute(context, values)

        self.check_list(result, "points", gom.Vec3d, None)
        self.check_list(result, "normals", gom.Vec3d, None)

        assert len(result["points"]) == len(result["normals"]), "The number of points and normals must be the same"

        return result


class Surface (ScriptedActual):
    '''
    Scripted actual surface element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        "vertices":  [(x: float, y: float, z: float), ...], // List of vertices
        "triangles": [(i1: int, i2: int, i3: int), ...]     // List of triangles (vertices' indices)
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='surface', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class SurfaceDefects (ScriptedActual):
    '''
    Scripted actual surface defects element
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='surface_defects', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class Volume (ScriptedActual):
    '''
    Scripted actual volume element

    The expected parameters from the element's `compute ()` function is a map with the following format:

    ```
    {
        'voxel_data': data: np.array (shape=(x, y, z), dtype=np.float32), // Voxels of the volume
        'transformation': (x: float, y: float, z: float)                  // Transformation of the volume
    }
    ```
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='volume', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class VolumeSegmentation (ScriptedActual):
    '''
    Scripted actual volume segmentation element
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='volume_segmentation', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class VolumeRegion (ScriptedActual):
    '''
    Scripted actual volume region element
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='volume_region', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class VolumeSection (ScriptedActual):
    '''
    Scripted actual volume section element
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='volume_section', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class VolumeDefects (ScriptedActual):
    '''
    Scripted actual volume defects element
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='volume_defects', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)


class VolumeDefects2d (ScriptedActual):
    '''
    Scripted actual 2d volume defects element
    '''

    def __init__(self, id: str, description: str, help_id: str = None):
        super().__init__(id=id, description=description, element_type='volume_defects_2d', help_id=help_id)

    def compute_stage(self, context, values):
        return self.compute(context, values)
