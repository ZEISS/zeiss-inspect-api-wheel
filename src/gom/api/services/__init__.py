#
# API declarations for gom.api.services
#
# @brief API for accessing the script based API extensions (services)
# 
# This API enables access to the script based API endpoint implementations, called 'services'.
# Each service is a script which is started in a server mode and adds various functions and
# endpoints to the ZEISS Inspect API.
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

class Service (gom.__api__.Object):
  '''
  @brief Class representing a single API service
  
  This class represents an API service. The properties of that service can be read and
  the service can be administered (started, stopped, ...) via that handle.
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def get_name(self) -> str:
    '''
    @brief Return the human readable name of this service
    @version 1
    @return Service name if the service is initialized
    '''
    return self.__call_method__('get_name')

  def get_endpoint(self) -> str:
    '''
    @brief Return the API endpoint name of this service
    @version 1
    
    This function returns the endpoint identifier this service is covering, like 'gom.api.services'.
    
    @return Service endpoint if the service is initialized
    '''
    return self.__call_method__('get_endpoint')

  def get_autostart(self) -> bool:
    '''
    @brief Return autostart status of the service
    
    This function returns if the service is started automatically at application startup. This
    status can only be set manually by the user either during service installation or afterwards in
    the service management dialog.
    
    @return 'true' if the service is started automatically at application startup
    '''
    return self.__call_method__('get_autostart')

  def get_number_of_instances(self) -> int:
    '''
    @brief Get the number of API instances (processes) the service runs in parallel
    
    Return the number of API processes instances which are running in parallel. A service can
    be configured to start more than one API process for parallelization.
    
    @return Number of API instances which are run in parallel when the service is started.
    '''
    return self.__call_method__('get_number_of_instances')

  def get_status(self) -> str:
    '''
    @brief Return the current service status
    @version 1
    
    This function returns the status the service is currently in. Possible values are
    
    - STOPPED: Service is not running.
    - STARTED: Service has been started and is currently initializing. This can include both the general
    service process startup or running the global service initialization code (model loading, ...).
    - RUNNING: Service is running and ready to process API requests. If there are multiple service instances configured
    per service, the service counts as RUNNING not before all of these instances have been initialized !
    - STOPPING: Service is currently shutting down,
    
    @return Service status
    '''
    return self.__call_method__('get_status')

  def start(self) -> None:
    '''
    @brief Start service
    @version 1
    
    This function will start a script interpreter executing the service script as an API endpoint.
    
    ```{caution}
    The function will return immediately, the service instances are starting in the background afterwards.
    The `get_status ()` function can be used to poll the status until the service has been started.
    ```
    '''
    return self.__call_method__('start')

  def stop(self) -> None:
    '''
    @brief Stop service
    @version 1
    
    Stop service. The service can be restarted afterwards via the 'start ()' function
    if needed.
    
    ```{caution}
    The function will return immediately, the service instances will be stopped asynchronously.
    The 'get_status ()' function can be used to poll the service status until all service instances
    have been stopped.
    ```
    '''
    return self.__call_method__('stop')


def get_services() -> [Service]:
  '''
  @brief Return the list of all running and not running services
  @version 1
  
  This function returns the listof registered services
  
  **Example:**
  
  ```
  for s in gom.api.services.get_services ():
    print (s.get_name ())
  > 'Advanced fitting algorithms'
  > 'Tube inspection diagrams'
  > ...
  ```
  
  @return The list of all registered services
  '''
  return gom.__api__.__call_function__()

