#
# API declarations for gom.api.project
#
# @brief Access to project relevant structures
# 
# This module contains functions for accessing project relevant data
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

class ProgressInformation (gom.__api__.Object):
  '''
  @deprecated Please use gom.api.progress.ProgressBar instead
  
  @brief Auxillary class allowing to set progress information
  
  This class is used to access the progress bar and progress message widgets of the application.
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def set_percent(self, percent:float) -> None:
    '''
    @deprecated Please use gom.api.progress.ProgressBar instead
    
    @brief Set progress value from 0 to 100 percent
    @version 1
    
    @param percent Progress bar value in percent (0...100)
    '''
    return self.__call_method__('set_percent', percent)

  def set_message(self, text:str) -> None:
    '''
    @deprecated Please use gom.api.progress.ProgressBar instead
    
    @brief Set progress message
    @version 1
    
    @param text Message to be displayed in the progress displaying widget
    '''
    return self.__call_method__('set_message', text)


def get_image_acquisition(measurement:object, camera:str, stage:int) -> object:
  '''
  @brief Generate an of image acquisition object which can be used to query images from the application
  @version 1
  
  This function returns an image acquisition object, which in turn can then be used to query the application for
  various image variants.
  
  Valid valid for the `camera` parameter are:
  - `left camera`: Left camera in a two camera system or the only existing camera in a single camera system
  - `right camera`: Right camera in a two camera system
  - `photogrammetry`: Photogrammetry (TRITOP) camera
  
  **Example**
  
  ```
  measurement = gom.app.project.measurement_series['Deformation series'].measurements['D1']
  stage = gom.app.project.stages['Stage 1']
  
  left = gom.api.project.get_image_acquisition (measurement, 'left camera', [stage.index])[0]
  right = gom.api.project.get_image_acquisition (measurement, 'right camera', [stage.index])[0]
  ```
  
  @param measurement Measurement the image is to be queried from.
  @param camera      Identifier for the camera which contributed to the measurement. See above for valid values.
  @param stage       Id of the stage for which the image acquisition object will access.
  @return Image acquisition object which can be used to fetch the images.
  '''
  return gom.__api__.__call_function__(measurement, camera, stage)

def get_image_acquisitions(measurement_list:object, camera:str, stage:int) -> object:
  '''
  @brief Generate a list of image acquisition objects which can be used to query images from the application
  @version 1
  
  This function returns a list of  image acquisition objects, which in turn can then be used to query the application
  for various image variants.
  
  Valid valid for the `camera` parameter are:
  - `left camera`: Left camera in a two camera system or the only existing camera in a single camera system
  - `right camera`: Right camera in a two camera system
  - `photogrammetry`: Photogrammetry (TRITOP) camera
  
  **Example**
  
  ```
  measurements = list (gom.app.project.measurement_series['Deformation series'].measurements)
  stage = gom.app.project.stages['Stage 1']
  point = gom.app.project.actual_elements['Point 1'].coordinate
  
  all_left_images = gom.api.project.get_image_acquisitions (measurements, 'left camera', [stage.index])
  all_right_images = gom.api.project.get_image_acquisitions (measurements, 'right camera', [stage.index])
  ```
  
  @param measurement Measurement the image is to be queried from.
  @param camera      Identifier for the camera which contributed to the measurement. See above for valid values.
  @param stage       Id of the stage for which the image acquisition object will access.
  @return Image acquisition object which can be used to fetch the images.
  '''
  return gom.__api__.__call_function__(measurement_list, camera, stage)

def create_progress_information() -> ProgressInformation:
  '''
  @deprecated Please use gom.api.progress.ProgressBar instead
  
  @brief Retrieve a progress information object which can be used to query/control progress status information
  @version 1
  
  This function returns an internal object which can be used to query/control the progress status widget of the
  main application window. It can be used to display progress information of long running processes.
  
  @return Progress information object
  '''
  return gom.__api__.__call_function__()

