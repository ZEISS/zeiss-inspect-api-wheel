#
# API declarations for gom.api.introspection
#
# @brief Introspection API for accessing the available API modules, functions and classes
# 
# This API enables access to the API structure in general. It is meant to be mainly for debugging and
# testing purposes.
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

class Function (gom.__api__.Object):
  '''
  @brief Introspection interface for a function
  
  This interface can be used to query various information about a function
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def name(self) -> str:
    '''
    @brief Returns the name of the function
    @version 1
    
    @return Function name
    '''
    return self.__call_method__('name')

  def descripion(self) -> str:
    '''
    @brief Returns the optional function description
    @version 1
    
    @return Function description
    '''
    return self.__call_method__('descripion')

  def signature(self) -> list[str]:
    '''
    @brief Returns the function signature
    @version 1
    
    The first type in the returned list is the function return value.
    
    @return Function signature
    '''
    return self.__call_method__('signature')

  def arguments(self) -> list[[str, str, str]]:
    '''
    @brief Returns detailed information about the function arguments
    @version 1
    
    @return Function arguments information
    '''
    return self.__call_method__('arguments')

  def returns(self) -> [str, str]:
    '''
    @brief Returns detailed information about the function returned value
    @version 1
    
    @return Function returned value information
    '''
    return self.__call_method__('returns')


class Module (gom.__api__.Object):
  '''
  @brief Introspection interface for a module
  
  This interface can be used to query various information about a module
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def name(self) -> str:
    '''
    @brief Returns the name of the module
    @version 1
    
    @return Module name
    '''
    return self.__call_method__('name')

  def version(self) -> int:
    '''
    @brief Returns the version of the module
    @version 1
    
    @return Module version
    '''
    return self.__call_method__('version')

  def description(self) -> str:
    '''
    @brief Returns the optional module description
    @version 1
    
    @return Module description
    '''
    return self.__call_method__('description')

  def tags(self) -> list[str]:
    '''
    @brief Returns the tags of the module
    @version 1
    
    Each module can have a set of tags classifying it or its properties.
    
    @return Module tags
    '''
    return self.__call_method__('tags')

  def functions(self) -> list[Function]:
    '''
    @brief Returns all available function of the module
    @version 1
    
    @return Module functions
    '''
    return self.__call_method__('functions')


class Method (gom.__api__.Object):
  '''
  @brief Introspection interface for a method
  
  This interface can be used to query various information about a method
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def name(self) -> str:
    '''
    @brief Returns the name of the method
    @version 1
    
    @return Method name
    '''
    return self.__call_method__('name')

  def description(self) -> str:
    '''
    @brief Returns the optional method description
    @version 1
    
    @return Method description
    '''
    return self.__call_method__('description')

  def signature(self) -> list[str]:
    '''
    @brief Returns the method signature
    @version 1
    
    This function returns the signature. The first type in the list is the expected return value
    
    @return Method signature in form of list
    '''
    return self.__call_method__('signature')

  def arguments(self) -> list[[str, str, str]]:
    '''
    @brief Returns detailed information about the method arguments
    @version 1
    
    @return Method argument information
    '''
    return self.__call_method__('arguments')

  def returns(self) -> [str, str]:
    '''
    @brief Returns detailed information about the return value
    @version 1
    
    @return Return value information
    '''
    return self.__call_method__('returns')


class Class (gom.__api__.Object):
  '''
  @brief Introspection interface for a class
  
  This interface can be used to query various information about a class definition
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def name(self) -> str:
    '''
    @brief Returns the name of the class
    @version 1
    
    @return Class name
    '''
    return self.__call_method__('name')

  def description(self) -> str:
    '''
    @brief Returns and optional class description
    @version 1
    
    @return Class description
    '''
    return self.__call_method__('description')

  def type(self) -> str:
    '''
    @brief Returns the unique internal type name of the class
    @version 1
    
    @return Type name
    '''
    return self.__call_method__('type')

  def methods(self) -> list[Method]:
    '''
    @brief Returns all class methods
    @version 1
    
    @return List of class methods
    '''
    return self.__call_method__('methods')


def modules() -> list[Module]:
  '''
  @brief Return a list of available modules
  @version 1
  
  This function can be used to query the modules of the API
  
  **Example:**
  
  ```
  for m in gom.api.introspection.modules ():
    print (m.name ())
  ```
  
  @return List of 'Module' objects.
  '''
  return gom.__api__.__call_function__()

def classes() -> Class:
  '''
  @brief Return introspection interface for a class instance
  @version 1
  
  @param instance 'Class' instance to inspect
  @return Introspection object
  '''
  return gom.__api__.__call_function__()

