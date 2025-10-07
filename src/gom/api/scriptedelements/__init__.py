#
# API declarations for gom.api.scriptedelements
#
# @brief API for handling scripted elements
# 
# This API defines various functions for handling scripted elements (actuals, inspections, nominal, diagrams, ...)
# It is used mostly internally by the scripted element framework.
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

def get_inspection_definition(typename:str) -> Any:
  '''
  @brief Return information about the given scripted element type
  
  This function queries in internal 'scalar registry' database for information about the
  inspection with the given type.
  
  @param type_name Type name of the inspection to query
  @return Dictionary with relevant type information or an empty dictionary if the type is unknown
  '''
  return gom.__api__.__call_function__(typename)

def get_dimension_definition(typename:str) -> Any:
  '''
  @brief Return information about the given dimension
  
  A physical dimension (or just "dimension") refers to the fundamental nature of what is measured - like length,
  time, mass, temperature, angle, etc. These represent the qualitative aspect of measurement. This is different
  from a unit: Unit refers to the specific standard of measurement used to quantify that dimension - like meter,
  millimeter, inch for length; or degree, radian for angle.
  
  @param name Name of the dimension
  @return Dictionary with relevant dimension information or an empty dictionary if the name does not refer to a dimension
  '''
  return gom.__api__.__call_function__(typename)

def get_dimensions() -> [str]:
  '''
  @brief Return available dimensions
  
  @return List of known dimensions
  '''
  return gom.__api__.__call_function__()

