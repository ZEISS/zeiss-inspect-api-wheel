#
# API declarations for gom.api.addons
#
# @brief API for accessing the add-ons currently installed in the running software instance
# 
# This API enables access to the installed add-ons. Information about these add-ons can be
# queried, add-on files and resources can be read and if the calling instance is a member of
# one specific add-on, this specific add-on can be modified on-the-fly and during software
# update processes.
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

class AddOn (gom.__api__.Object):
  '''
  @brief Class representing a single add-on
  
  This class represents a single add-on. Properties of that add-on can be queried from here.
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def get_id(self) -> UUID:
    '''
    @brief Return the unique id (uuid) of this add-on
    @version 1
    
    This function returns the uuid associated with this add-on. The id can be used to
    uniquely address the add-on.
    
    @return Add-on uuid
    '''
    return self.__call_method__('get_id')

  def get_name(self) -> str:
    '''
    @brief Return the displayable name of the add-on
    @version 1
    
    This function returns the displayable name of the add-on. This is the human
    readable name which is displayed in the add-on manager and the add-on store.
    
    @return Add-on name
    '''
    return self.__call_method__('get_name')

  def get_file(self) -> str:
    '''
    @brief Return the installed add-on file
    @version 1
    
    This function returns the installed ZIP file representing the add-on. The file might be
    empty if the add-on has never been 'completed'. If the add-on is currently in edit mode,
    instead the edit directory containing the unpacked add-on sources is returned. In any way,
    this function returns the location the application uses, too, to access add-on content.
    
    @return Add-on file path (path to the add-ons installed ZIP file) or add-on edit directory if the add-on is currently in edit mode.
    '''
    return self.__call_method__('get_file')

  def get_level(self) -> str:
    '''
    @brief Return the level (system/shared/user) of the add-on
    @version 1
    
    This function returns the 'configuration level' of the add-on. This can be
    * 'system' for pre installed add-on which are distributed together with the application
    * 'shared' for add-ons in the public or shared folder configured in the application's preferences or
    * 'user' for user level add-ons installed for the current user only.
    
    @return Level of the add-on
    '''
    return self.__call_method__('get_level')

  def is_edited(self) -> bool:
    '''
    @brief Return if the add-on is currently edited
    @version 1
    
    Usually, an add-on is simply a ZIP file which is included into the applications file system. When
    an add-on is in edit mode, it will be temporarily unzipped and is then present on disk in a directory.
    
    @return 'true' if the add-on is currently in edit mode
    '''
    return self.__call_method__('is_edited')

  def is_protected(self) -> bool:
    '''
    @brief Return if the add-on is protected
    @version 1
    
    The content of a protected add-on is encrypted. It can be listed, but not read. Protection
    includes both 'IP protection' (content cannot be read) and 'copy protection' (content cannot be
    copied, as far as possible)
    
    @return Add-on protection state
    '''
    return self.__call_method__('is_protected')

  def has_license(self) -> bool:
    '''
    @brief Return if the necessary licenses to use this add-on are present
    @version 1
    
    This function returns if the necessary licenses to use the add-on are currently present.
    Add-ons can either be free and commercial. Commercial add-ons require the presence of a
    matching license via a license dongle or a license server.
    '''
    return self.__call_method__('has_license')

  def get_tags(self) -> str:
    '''
    @brief Return the list of tags with which the add-on has been tagged
    @version 1
    
    This function returns the list of tags in the addons `metainfo.json` file.
    
    @return List of tags
    '''
    return self.__call_method__('get_tags')

  def get_file_list(self) -> list:
    '''
    @brief Return the list of files contained in the add-on
    @version 1
    
    This function returns the list of files and directories in an add-on. These path names can
    be used to read or write/modify add-on content.
    
    Please note that the list of files can only be obtained for add-ons which are currently not
    in edit mode ! An add-on in edit mode is unzipped and the `get_file ()` function will return
    the file system path to its directory in that case. That directory can then be browsed with
    the standard file tools instead.
    
    #### Example
    
    ```
    for addon in gom.api.addons.get_installed_addons():
      # Edited add-ons are file system based and must be accessed via file system functions
      if addon.is_edited():
        for root, dirs, files in os.walk(addon.get_file ()):
          for file in files:
            print(os.path.join(root, file))
    
      # Finished add-ons can be accessed via this function
      else:
        for file in addon.get_file_list():
          print (file)
    ```
    
    @return List of files in that add-on (full path)
    '''
    return self.__call_method__('get_file_list')

  def get_content_list(self) -> list:
    '''
    @brief Return the list of contents contained in the add-on
    @version 1
    
    @return List of contents in that add-on (full path)
    '''
    return self.__call_method__('get_content_list')

  def get_script_list(self) -> list:
    '''
    @brief Return the list of scripts contained in the add-on
    @version 1
    
    @return List of scripts in that add-on (full path)
    '''
    return self.__call_method__('get_script_list')

  def get_version(self) -> str:
    '''
    @brief Return the version of the add-on
    @version 1
    
    @return Add-on version in string format
    '''
    return self.__call_method__('get_version')

  def get_required_software_version(self) -> str:
    '''
    @brief Return the minimum version of the ZEISS INSPECT software required to use this add-on
    @version 1
    
    By default, an add-on is compatible with the ZEISS INSPECT software version it was created in and
    all following software version. This is the case because it can be assumed that this add-on is
    tested with that specific software version, not with any prior version, leading to a minimum requirement.
    On the other hand, the software version where an add-on then later will break because of incompatibilities
    cannot be foreseen at add-on creation time. Thus, it is also assumed that a maintainer cares for an
    add-on and updates it to the latest software version if necessary. There cannot be a "works until" entry
    in the add-on itself, because this would require to modify already released version as soon as this specific
    version which breaks the add-on becomes known.
    
    @return Addon version in string format
    '''
    return self.__call_method__('get_required_software_version')

  def exists(self, path:str) -> bool:
    '''
    @brief Check if the given file or directory exists in an add-on
    @version 1
    
    This function checks if the given file exists in the add-on
    
    @param path File path as retrieved by 'gom.api.addons.AddOn.get_file_list ()'
    @return 'true' if a file or directory with that name exists in the add-on
    '''
    return self.__call_method__('exists', path)

  def read(self, path:str) -> bytes:
    '''
    @brief Read file from add-on
    @version 1
    
    This function reads the content of a file from the add-on. If the add-on is protected,
    the file can still be read but will be AES encrypted.
    
    **Example:** Print all add-on 'metainfo.json' files
    
    ```
    import gom
    import json
    
    for a in gom.api.addons.get_installed_addons ():
      text = json.loads (a.read ('metainfo.json'))
      print (json.dumps (text, indent=4))
    ```
    
    @param path File path as retrieved by 'gom.api.addons.AddOn.get_file_list ()'
    @return Content of that file as a byte array
    '''
    return self.__call_method__('read', path)

  def write(self, path:str, data:bytes) -> None:
    '''
    @brief Write data into add-on file
    @version 1
    
    This function writes data into a file into an add-ons file system. It can be used to update,
    migrate or adapt the one add-on the API call originates from. Protected add-ons cannot be
    modified at all.
    
    ```{important}
    An add-on can modify only its own content ! Access to other add-ons is not permitted. Use this
    function with care, as the result is permanent !
    ```
    
    @param path File path as retrieved by 'gom.api.addons.AddOn.get_file_list ()'
    @param data Data to be written into that file
    '''
    return self.__call_method__('write', path, data)


def get_installed_addons() -> list[AddOn]:
  '''
  @brief Return a list of the installed add-ons
  @version 1
  
  This function can be used to query information of the add-ons which are currently
  installed in the running instance.
  
  **Example:**
  
  ```
  for a in gom.api.addons.get_installed_addons ():
    print (a.get_id (), a.get_name ())
  ```
  
  @return List of 'AddOn' objects. Each 'AddOn' object represents an add-on and can be used to query information about that specific add-on.
  '''
  return gom.__api__.__call_function__()

def get_current_addon() -> AddOn:
  '''
  @brief Return the current add-on
  @version 1
  
  This function returns the add-on the caller is a member of
  
  **Example:**
  
  ```
  addon = gom.api.addons.get_current_addon ()
  print (addon.get_id ())
  > d04a082c-093e-4bb3-8714-8c36c7252fa0
  ```
  
  @return Add-on the caller is a member of or `None` if there is no such add-on
  '''
  return gom.__api__.__call_function__()

def get_addon(id:UUID) -> AddOn:
  '''
  @brief Return the add-on with the given id
  @version 1
  
  This function returns the add-on with the given id
  
  **Example:**
  
  ```
  addon = gom.api.addons.get_addon ('1127a8be-231f-44bf-b15e-56da4b510bf1')
  print (addon.get_name ())
  > 'AddOn #1'
  ```
  
  @param id Id of the add-on to get
  @return Add-on with the given id
  @throws Exception if there is no add-on with that id
  '''
  return gom.__api__.__call_function__(id)

