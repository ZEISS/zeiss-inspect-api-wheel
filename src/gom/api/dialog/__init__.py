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

def create(context:Any, url:str) -> Any:
  '''
  @brief Create modal dialog, but do not execute it yet
  
  This function creates a dialog. The dialog is passed in an abstract JSON description defining its layout.
  The dialog is created but not executed yet. The dialog can be executed later by calling the 'gom.api.dialog.show'
  function. The purpose of this function is to create a dialog in advance and allow the user setting it up before
  
  This function is part of the scripted contribution framework. It can be used in the scripts
  'dialog' functions to pop up user input dialogs, e.g. for creation commands. Passing of the
  contributions script context is mandatory for the function to work.
  
  @param context Script execution context
  @param url     URL of the dialog definition (*.gdlg file)
  @return Dialog handle which can be used to set up the dialog before executing it
  '''
  return gom.__api__.__call_function__(context, url)

def show(context:Any, dialog:Any) -> Any:
  '''
  @brief Show previously created and configured dialog
  
  This function shows and executes previously created an configured dialog. The combination of
  'create' and 'show' in effect is the same as calling 'execute' directly.
  
  @param context Script execution context
  @param dialog  Handle of the previously created dialog
  @return Dialog input field value map. The dictionary contains one entry per dialog widget with that widgets current value.
  '''
  return gom.__api__.__call_function__(context, dialog)

def execute(context:Any, url:str) -> Any:
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
  return gom.__api__.__call_function__(context, url)

