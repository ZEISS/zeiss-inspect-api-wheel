#
# API declarations for gom.api.imaging
#
# @brief Image point/pixel related functions
# 
# Image related functions can be used to query images from the measurements of a project. This is not done directly,
# but via an ‘image acquisition’ object which acts as a proxy between the image storing data structure and the
# functions which can be used to process the image data.
# 
# Terminology:
# - 'point': 3D coordinate in the project.
# - 'pixel': 2D coordinate in an image.
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

class Acquisition (gom.__api__.Object):
  '''
  @brief Class representing a single acquisition
  
  An acquisition describes a camera position and viewing direction of a measurement.
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def get_coordinate(self) -> gom.Vec3d:
    '''
    @brief Return 3d coordinate of the camera during the measurement
    '''
    return self.__call_method__('get_coordinate')

  def get_angle(self) -> gom.Vec3d:
    '''
    @brief Return viewing angles of the camera during the measurement
    '''
    return self.__call_method__('get_angle')


def compute_point_from_pixels(pixel_and_image_acquisitions:[list], use_calibration:bool) -> [list]:
  '''
  @brief Compute 3d point coordinates from pixels in images
  @version 1
  
  This function is used to compute 3d points matching to 2d points in a set of images. The input parameter is a list
  containing a list of tuples where each tuple consists of a 2d pixel and the matching acquisition object. The
  acquisition object is then used to compute the location of the 3d point from the pixels in the referenced images.
  Usually at least two tuples with matching pixels from different images are needed to compute a 3d point. An exception
  are projects with 2d deformation measurement series. Only there it is sufficient to pass one tuple per point to the
  function.
  
  The user has to make sure that the pixels from different tuples are matching, which means they correspond to the same
  location on the specimen. You can use the function gom.api.imaging.compute_epipolar_line() as a helper.
  
  The returned value is a list of (point, residuum) where each entry is the result of intersecting rays cast from the
  camera positions through the given pixels. The pixel coordinate system center is located in the upper left corner.
  
  **Example**
  
  ```
  measurement = gom.app.project.measurement_series['Deformation 1'].measurements['D1']
  stage = gom.app.project.stages[0]
  
  img_left = gom.api.project.get_image_acquisition (measurement, 'left camera', [stage.index])[0]
  img_right = gom.api.project.get_image_acquisition (measurement, 'right camera', [stage.index])[0]
  
  pixel_pair_0 = [(gom.Vec2d(1587.74, 793.76), img_left), (gom.Vec2d(2040.22, 789.53), img_right)]
  pixel_pair_1 = [(gom.Vec2d(1617.47, 819.67), img_left), (gom.Vec2d(2069.42, 804.69), img_right)]
  
  tuples = [pixel_pair_0, pixel_pair_1]
  points = gom.api.imaging.compute_point_from_pixels(tuples, False)
  
  print (points)
  ```
  
  ```
  [[gom.Vec3d (-702.53, 1690.84, -22.37), 0.121], [gom.Vec3d (-638.25, 1627.62, -27.13), 0.137]]
  ```
  
  @param pixel_and_image_acquisitions List of (pixel, acquisition) tuples
  @param use_calibration If set, the information from the calibration is used to compute the point. Project must provide a calibration for that case.
  @return List of matching pixels and residuums
  '''
  return gom.__api__.__call_function__(pixel_and_image_acquisitions, use_calibration)

def compute_pixels_from_point(point_and_image_acquisitions:list[tuple[gom.Vec3d, gom.Object]]) -> list[gom.Vec2d]:
  '''
  @brief Compute pixel coordinates from point coordinates
  @version 1
  
  This function is used to compute the location of a 3d point in a 2d image. This is a photogrammetric
  operation which will return a precise result. The input parameter is a list of tupels where each tuple consists
  of a 3d point and and acquisition object. The acquisition object is then used to compute the location of the
  3d point in the referenced image. This might lead to multiple pixels as a result, so the return value is again
  a list containing 0 to n entries of pixel matches.
  
  **Example**
  
  ```
  measurement = gom.app.project.measurement_series['Deformation series'].measurements['D1']
  stage = gom.app.project.stages['Stage 1']
  point = gom.app.project.actual_elements['Point 1'].coordinate
  
  left = gom.api.project.get_image_acquisition (measurement, 'left camera', [stage.index])[0]
  right = gom.api.project.get_image_acquisition (measurement, 'right camera', [stage.index])[0]
  
  p = gom.api.imaging.compute_pixels_from_point ([(point, left), (point, right)])
  
  print (p)
  ```
  
  ```
  [gom.Vec2d (1031.582008690226, 1232.4155555222544), gom.Vec2d (1139.886626169376, 1217.975608783256)]
  ```
  
  @param point_and_image_acquisitions List of (point, acquisition) tuples
  @return List of matching points
  '''
  return gom.__api__.__call_function__(point_and_image_acquisitions)

def compute_epipolar_line(source:Acquisition, traces:list[tuple[gom.Vec2d, gom.Object]], max_distance:float) -> list[list[gom.Vec2d]]:
  '''
  @brief Compute epipolar line coordinates
  @version 1
  
  This function computes the parametrics of an epipolar line from pixels projected into images.
  
  **Example**
  
  ```
  stage = gom.app.project.stages['Stage 1']
  point = gom.app.project.actual_elements['Point 1'].coordinate
  
  left = gom.api.project.get_image_acquisition (measurement, 'left camera', [stage.index])[0]
  right = gom.api.project.get_image_acquisition (measurement, 'right camera', [stage.index])[0]
  
  l = gom.api.imaging.compute_epipolar_line (left, [(gom.Vec2d (1617, 819), right)], 10.0)
  
  print (l)
  ```
  
  ```
  [[gom.Vec2d (4.752311764226988, 813.7915394509045), gom.Vec2d (10.749371580282741, 813.748887458453), gom.Vec2d
  (16.73347976996274, 813.706352662515), ...]]
  ```
  
  @param source Handle of the image acquisition the epipolar line should be found in.
  @param traces List of pairs where each entry describes a pixel image coordinate plus the image acquisition object which should be used to compute the matching point. The image acquisition object here is the “other” acquisition providing the pixels used to find the matching epipolar lines in the `sources` object.
  @param max_distance Maximum search distance in mm.
  @return List of matching points
  '''
  return gom.__api__.__call_function__(source, traces, max_distance)

