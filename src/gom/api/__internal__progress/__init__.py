#
# API declarations for gom.api.__internal__progress
#
# @nodoc
# 
# @brief Internal API for accessing the progress bar in the main window
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

class InternalProgressBar (gom.__api__.Object):
  '''
  @nodoc
  
  @brief Class representing the internal ProgressBar
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def _register_watcher(self) -> None:
    '''
    @nodoc
    
    @brief Only for internal use!
    '''
    return self.__call_method__('_register_watcher')

  def _deregister_watcher(self) -> None:
    '''
    @nodoc
    
    @brief Only for internal use!
    '''
    return self.__call_method__('_deregister_watcher')

  def _set_progress(self, progress:int) -> None:
    '''
    @nodoc
    
    @brief Sets the progress in the main window progress bar
    @version 1
    
    @param progress in percent, given as an integer from 0 to 100
    @return nothing
    '''
    return self.__call_method__('_set_progress', progress)

  def _set_message(self, message:str) -> None:
    '''
    @nodoc
    
    @brief Sets a message in the main window progress bar
    @version 1
    
    @param message the message to display
    @return nothing
    '''
    return self.__call_method__('_set_message', message)


def _create_internal_progress_bar(passcode:str) -> None:
  '''
  gom.api.__internal__progress.InternalProgressBar
  
  @nodoc
  
  @brief Only for internal use!
  '''
  return gom.__api__.__call_function__(passcode)

