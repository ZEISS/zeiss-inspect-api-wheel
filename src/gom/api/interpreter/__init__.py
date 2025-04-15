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

def __enter_multi_element_creation_scope__() -> None:
  '''
  @brief Mark the start of a multi element creation block
  
  ```{warning}
  Do not use these internal functions directly ! Use the `with` statement format as described in the
  documentation below instead for an exception safe syntax.
  ```
  
  This internal function can be used to disable the signal generation which usually triggers a full ZEISS INSPECT
  synchronization after each element creation. This is useful when creating multiple elements in a row to avoid
  unnecessary overhead. The block has to be closed with the '__exit_multi_creation_block__' function, which is done
  automatically if the corresponding `with` statement syntax as explained in the example below is used. Please be aware
  that disabling full synchronization points can lead to side effects - use this feature with case and well considered
  !
  
  **Example**
  
  ```
  with gom.api.tools.MultiElementCreationScope ():
      for _ in range (1000):
          gom.script.sys.create_some_simple_point (...)
  
  # Synchronization signal is emitted here. Application is sync'ed and valid afterwards again.
  
  gom.script.sys.continue_with_some_other_stuff (...)
  ```
  '''
  return gom.__api__.__call_function__()

def __exit_multi_element_creation_scope__() -> None:
  '''
  @brief Mark the end of a multi element creation block
  
  See `gom.api.interpreter.__enter_multi_element_creation_scope__` for details.
  '''
  return gom.__api__.__call_function__()

