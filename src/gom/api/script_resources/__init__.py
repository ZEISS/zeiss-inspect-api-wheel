#
# API declarations for gom.api.script_resources
#
# @brief API for the ResourceDataLoader
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

def list() -> list[str]:
  '''
  @brief Return the list of existing resources
  
  @return List of existing resources
  '''
  return gom.__api__.__call_function__()

def create(path:str) -> bool:
  '''
  @brief Create a new resource under the root folder of a given script, if not already present.
  
  @param path Resource path
  @return `true` if a valid resource was found or created.
  '''
  return gom.__api__.__call_function__(path)

def load(path:str, size:int) -> str:
  '''
  @brief Load resource into shared memory
  
  @param path Resource path
  @param size Buffer size
  @return Shared memory key of the loaded resource
  '''
  return gom.__api__.__call_function__(path, size)

def unload(path:str) -> bool:
  '''
  @brief Unload resource from shared memory
  
  @param path Resource path
  @return 'True' if the unloading succeeded
  '''
  return gom.__api__.__call_function__(path)

def save(path:str, size:int) -> bool:
  '''
  @brief Save resource changes from shared memory
  
  @param path Resource path
  @param size Buffer size
  @return 'True' if the data could be written
  '''
  return gom.__api__.__call_function__(path, size)

def save_as(old_path:str, new_path:str, overwrite:bool) -> bool:
  '''
  @brief Save resource changes from shared memory at new path
  
  @param old_path Old resource path
  @param new_path New resource path
  @param size Buffer size
  @return 'True' if the data could be written
  '''
  return gom.__api__.__call_function__(old_path, new_path, overwrite)

def mem_size(path:str) -> int:
  '''
  @brief Return size of the resource shared memory segment
  
  @param path Resource path
  @return Shared memory segment size
  '''
  return gom.__api__.__call_function__(path)

def exists(path:str) -> bool:
  '''
  @brief Check if the resource with the given path exists
  
  @param path Resource path
  @return 'True' if a resource with that path exists
  '''
  return gom.__api__.__call_function__(path)

