#
# API declarations for gom.api.testing
#
# @brief API with testing and verification functions
# 
# ```{caution}
# This API is for internal debugging purposes ! Its content format may change arbitrarily !
# ```
# 
# This API provides various functions which can be of use when testing and developing
# API features.
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

class TestObject (gom.__api__.Object):
  '''
  @brief Simple object which can be passed around the API for testing purpose
  
  This object is used by various test setups to test object handling in the API
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def get_id(self) -> UUID:
    '''
    @brief Return the unique id (uuid) of this object
    @version 1
    
    This function returns the uuid associated with this object. The id is generated
    randomly when the object is generated.
    
    @return Object uuid
    '''
    return self.__call_method__('get_id')

  def get_name(self) -> str:
    '''
    @brief Return the name of this object
    @version 1
    
    This function returns the name of this object.
    
    @return Object name
    '''
    return self.__call_method__('get_name')


def reflect(content:Any) -> Any:
  '''
  @brief Send value to the API and return an echo
  @version 1
  
  This function is used for API testing. It just reflects the given value, so some conversions
  back and forth will be performed.
  
  **Example:**
  
  ```
  result = gom.api.testing.reflect ({'a': [1, 2, 3], 'b':('foo', 'bar')})
  ```
  
  @param value The value to be reflected
  @return Reflected value
  '''
  return gom.__api__.__call_function__(content)

def generate_test_object(content:str) -> TestObject:
  '''
  @brief Generate test object
  @version 1
  
  This function is used for API testing. It generates a simple test object which can then
  be passed around the API.
  
  **Example:**
  
  ```
  obj = gom.api.testing.generate_test_object('test1')
  ```
  
  @param name Name of the test object
  @return Test object instance
  '''
  return gom.__api__.__call_function__(content)

def get_env(name:str) -> str:
  '''
  @brief Return main process environment variable value
  @version 1
  
  Return the value of the environment variable with the given name. If the variable does not
  exist, an empty string is returned. The function is used for testing of the environment variable
  sharing properties between ZEISS INSPECT and its python processes. Please use the native python
  functions for environment variable access instead.
  
  **Example:**
  
  ```
  value = gom.api.testing.get_env('MY_ENVIRONMENT_VARIABLE')
  ```
  
  @param name Name of the environment variable to read
  @return Environment variable value
  '''
  return gom.__api__.__call_function__(name)

def set_env(name:str, value:str) -> str:
  '''
  @brief Set main process environment variable value
  @version 1
  
  Set the value of the environment variable with the given name. The function is used for
  testing of the environment variable sharing properties between ZEISS INSPECT and its
  python processes. Please use the native python functions for environment variable
  manipulation instead.
  
  **Example:**
  
  ```
  gom.api.testing.set_env('MY_ENVIRONMENT_VARIABLE', 'some_value')
  ```
  
  @param name Name of the environment variable to set
  @param value New value of the environment variable
  '''
  return gom.__api__.__call_function__(name, value)

