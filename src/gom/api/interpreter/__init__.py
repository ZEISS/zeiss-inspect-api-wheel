#
# API declarations for gom.api.interpreter
#
# @brief API for accessing python script interpreter properties
# 
# This API can access properties and states of the python script interpreters. It is used
# mainly for internal debugging and introspection scenarios.
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

def get_pid() -> int:
  '''
  @brief Return the process id (PID) of the API handling application
  
  This function returns the process id of the application the script is connected with.
  
  @return Application process id
  '''
  return gom.__api__.__call_function__()

def get_info() -> dict:
  '''
  @brief Query internal interpreter state for debugging purposed
  
  ```{caution}
  This function is for debugging purposes only ! Its content format may change arbitrarily !
  ```
  
  @return JSON formatted string containing various information about the running interpreters
  '''
  return gom.__api__.__call_function__()

