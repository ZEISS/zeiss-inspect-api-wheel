#
# API declarations for gom.api.settings
#
# @brief API for storing add-on related settings persistently
# 
# This API allows reading/writing values into the application configuration permantly. The
# configuration is persistant and will survive application restarts. Also, it can be accessed
# via the applications preferences dialog.
# 
# The configuration entries must be defined in the add-ons `metainfo.json` file. This configuration
# defined the available keys, the entry types and the entry properties. If the entry type can be
# represented by some widget, the setting entry will also be present in the applications 'preferences'
# dialog and can be adapted interactively there.
# 
# ### Example
# 
# ```
# {
#   "title": "Settings API example",
#   "description": "Example add-on demonstrating usage of the settings API",
#   "uuid": "3b515488-aa7b-4035-85e1-b9509db8af4f",
#   "version": "1.0.2",
#   "settings": [
#    {
#       "name": "dialog",
#       "description": "Dialog configuration"
#    },
#    {
#      "name": "dialog.size",
#      "description": "Size of the dialog"
#    },
#    {
#      "name": "dialog.size.width",
#      "description": "Dialog width",
#      "value": 640,
#      "digits": 0
#    },
#    {
#      "name": "dialog.size.height",
#      "description": "Dialog height",
#      "value": 480,
#      "digits": 0
#    },
#    {
#      "name": "dialog.threshold",
#      "description": "Threshold",
#      "value": 1.0,
#      "minimum": 0.0,
#      "maximum": 10.0,
#      "digits": 2,
#      "step": 0.01
#    },
#    {
#      "name": "dialog.magic",
#      "description": "Magic Key",
#      "value": "Default text",
#      "visible": false
#    },
#    {
#      "name": "enable",
#      "description": "Enable size storage",
#      "value": true,
#      "visible": true
#    },
#    {
#      "name": "dialog.file",
#      "description": "Selected file",
#      "value": "",
#      "type": "file",
#      "mode": "any",
#      "visible": true
#    }
#   ]
#  }
# ```
# 
# This will lead to configuration entries in the applications preferences. Given that the `metainfo.json` is
# part of an add-on called 'Settings API Example', the application preferences will contain the following items
# (visible setting entries only):
# 
# ![Settings level 1](images/settings_api_preferences_1.png)
# 
# ![Settings level 2](images/settings_api_preferences_2.png)
# 
# ### Types
# 
# See the examples above for how to configure the different settings type. Usually, the `value` field determines the
# type of the setting. For example, a `23` indicates that an integer is requested. A `23.0` with `digits` greater than
# 0 will lead to a float settings type.
# 
# Special non basic types are specified via the `type` field explicitly. For example, the file selector is configured
# if the `type` field has been set to `file`.
# 
# #### File selector
# 
# The file selector provides a `mode` attribute in addition to the standard settings entry attributes. The `mode`
# attribute determines what kind of files or directories can be selected.
# 
# - `any`: Any file
# - `new`: Any file not yet existing in a writable directory
# - `load_file`: Existing file with reading permissions
# - `load_files`: Multi existing files with reading permissions
# - `save_file`: Existing or new file with writing permissions
# - `load_dir`: Existing directory with reading permissions
# - `save_dir`: Existing directory with writing permissions
# - `exec`: Existing executable file
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

def get(key:str) -> Any:
  '''
  @brief Read value from application settings
  @version 1
  
  This function reads a value from the application settings. The value is referenced by a key. Supported value types
  are integer, double, string and bool.
  
  **Example**
  
  ```
  w = gom.api.settings.get ('dialog.width')
  h = gom.api.settings.get ('dialog.height')
  ```
  
  @param key     Configuration key. Must be a key as defined in the add-ons `metainfo.json` file.
  @return Configuration value for that key
  '''
  return gom.__api__.__call_function__(key)

def set(key:str, value:Any) -> None:
  '''
  @brief Write value into application settings
  @version 1
  
  This function writes a value into the application settings. The value is referenced by a key. Supported value types
  are integer, double, string and bool.
  
  **Example**
  
  ```
  gom.api.settings.set ('dialog.width', 640)
  gom.api.settings.set ('dialog.height', 480)
  ```
  
  @param key     Configuration key. Must be a key as defined in the add-ons `metainfo.json` file.
  @param value   Value to be written
  '''
  return gom.__api__.__call_function__(key, value)

def list() -> list[str]:
  '''
  @brief List all available keys for the current add-on
  @version 1
  
  This function returns a list of all available keys in the settings for the current add-on.
  These keys are the same configuration keys are used in the `metainfo.json` file of that add-on.
  
  @return List of all the keys in the settings which belong to the current add-on
  '''
  return gom.__api__.__call_function__()

