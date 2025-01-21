#
# API declarations for gom.api.dialog
#
# @brief API for handling dialogs
# 
# This API is used to create and execute script based dialogs. The dialogs are defined in a
# JSON based description format and can be executed server side in the native UI style.
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

def execute(context:Any, data:str) -> Any:
  '''
  @brief Create and execute a modal dialog
  
  This function creates and executes a dialog. The dialog is passed in an abstract JSON
  description and will be executed modal. The script will pause until the dialog is either
  confirmed or cancelled.
  
  This function is part of the scripted contribution framework. It can be used in the scripts
  'dialog' functions to pop up user input dialogs, e.g. for creation commands. Passing of the
  contributions script context is mandatory for the function to work.
  
  @param context Script execution context
  @param url     URL of the dialog definition (*.gdlg file)
  @return Dialog input field value map. The dictionary contains one entry per dialog widget with that widgets current value.
  '''
  return gom.__api__.__call_function__(context, data)

