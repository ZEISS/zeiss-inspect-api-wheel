#
# API declarations for gom.api.selection
#
# @brief API for handling explorer selection
# 
# This API defines functions for accessing and manipulating the current selection in the explorer.
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

def get_selected_elements() -> Any:
  '''
  @brief Returns the list of currently selected elements in the explorer
  
  This function returns the resolved list of single elements which are currently selected in the explorer. The
  selection mechanism as such is more complicated and selection of categories, groups, tags etc. is also possible.
  So the function is covering the very basic per element selection only.
  
  @return List of selected elements
  '''
  return gom.__api__.__call_function__()

