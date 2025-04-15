#
# API declarations for gom.api.scriptedelements
#
# @brief API for handling scripted elements
# 
# This API defines various functions for handling scripted elements (actuals, inspections, nominal, diagrams, ...)
# It is used mostly internal by the scripted element framework.
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

def get_unit_definition(typename:str) -> Any:
  '''
  @brief Return information about the given unit type
  
  @param name Name of the unit type
  @return Dictionary with relevant type information or an empty dictionary if the name does not refer to a unit class
  '''
  return gom.__api__.__call_function__(typename)

