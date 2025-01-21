#
# API declarations for gom.api.scripted_checks_util
#
# @brief Tool functions for scripted checks
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

def is_scalar_checkable(element:gom.Object) -> bool:
  '''
  @brief Checks if the referenced element is suitable for inspection with a scalar check
  @version 1
  
  This function checks if the given element can be inspected like a scalar value in the context of scripted
  elements. Please see the scripted element documentation for details about the underlying scheme.
  
  @param element Element reference to check
  @return 'true' if the element is checkable like a scalar value
  '''
  return gom.__api__.__call_function__(element)

def is_surface_checkable(element:gom.Object) -> bool:
  '''
  @brief Checks if the referenced element is suitable for inspection with a surface check
  @version 1
  
  This function checks if the given element can be inspected like a surface in the context of scripted
  elements. Please see the scripted element documentation for details about the underlying scheme.
  
  @param element Element reference to check
  @return 'true' if the element is checkable like a surface
  '''
  return gom.__api__.__call_function__(element)

def is_curve_checkable(element:gom.Object) -> bool:
  '''
  @brief Checks if the referenced element is suitable for inspection with a curve check
  @version 1
  
  This function checks if the given element can be inspected like a curve in the context of scripted
  elements. Please see the scripted element documentation for details about the underlying scheme.
  
  @param element Element reference to check
  @return 'true' if the element is checkable like a curve
  '''
  return gom.__api__.__call_function__(element)

