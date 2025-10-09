#
# API declarations for gom.api.infoitem
#
# @brief API for creating, configuring, and displaying info items
# 
# This API provides functions and classes to create, configure, and display info items
# within the application's graphical user interface. Info items can be shown as simple text
# or as structured content with headings, descriptions, and keyboard/mouse shortcuts.
# The API supports querying available categories and alignments, and allows dynamic control
# over the visibility, warning state, and content of each info item. Both plain text and
# structured info item types are supported, enabling flexible presentation of contextual
# information to the user.
# 
# ![Info Item Example](images/info_item_api_1.png)
# 
# Info items can be positioned in five different alignments: top, center, bottom, top_right, and top_left.
#

import gom
import gom.__api__

from typing import Any
from uuid import UUID

class Text (gom.__api__.Object):
  '''
  @brief Class for displaying simple text info items
  
  This class represents an info item that displays plain text within the application's graphical user interface.
  It provides methods to set the text content, control visibility, configure warning and always-visible states,
  and retrieve the current configuration. The text info item can be aligned in various positions and can use a larger
  font if specified.
  
  **Example:**
  ```
  import gom
  import gom.api.infoitem
  
  item_text = gom.api.infoitem.create_text('INFO_WARNING', 'top_left')
  item_text.set_text("Hello World")
  item_text.set_always_visible(True)
  item_text.show()
  ```
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def set_warning(self, state:bool) -> None:
    '''
    @brief Set the warning state for this text info item
    
    Sets whether this info item should be displayed in a warning state. When set to true,
    the item will be visually highlighted as a warning in the user interface.
    
    ![Info Item Structured Example](images/info_item_api_text_1.png)
    
    @param state If true, the item is marked as a warning; otherwise, it is shown normally.
    '''
    return self.__call_method__('set_warning', state)

  def set_always_visible(self, state:bool) -> None:
    '''
    @brief Set the always-visible state for this text info item
    
    Sets whether this info item should always be visible, regardless of its priority or other conditions.
    When set to true, the item will remain visible in the user interface at all times.
    
    @param state If true, the item is always visible; otherwise, it follows normal visibility rules.
    '''
    return self.__call_method__('set_always_visible', state)

  def get_configuration(self) -> dict:
    '''
    @brief Return the current configuration of this text info item as a dictionary
    
    This method returns the current configuration and state of the text info item as a dictionary.
    The configuration includes properties such as category, alignment, font size, warning state,
    always-visible state, and the current text content. This is mainly intended for debugging or
    inspection purposes.
    
    @return Dictionary containing the configuration of the text info item
    '''
    return self.__call_method__('get_configuration')

  def show(self) -> None:
    '''
    @brief Show this text info item in the user interface
    
    Displays the text info item in the application's graphical user interface using the current text content.
    '''
    return self.__call_method__('show')

  def clear(self) -> None:
    '''
    @brief Clear the content and hide this text info item
    
    Removes the text content from the info item and hides it from the user interface.
    '''
    return self.__call_method__('clear')

  def set_text(self, text:str) -> None:
    '''
    @brief Set the text content for this info item
    
    Sets the text that will be displayed by this info item. If the item is currently visible,
    the displayed content is updated immediately.
    
    **Example:**
    ```
    item_text.set_text("New message")
    ```
    
    @param text The new text to display in the info item
    '''
    return self.__call_method__('set_text', text)


class Structured (gom.__api__.Object):
  '''
  @brief Class for displaying structured info items
  
  This class represents an info item that displays structured content within the application's graphical user
  interface. Structured info items can include a heading (with optional icon and help id), a description, and one or
  more keyboard/mouse shortcuts. The class provides methods to set and update each of these fields, as well as to
  control visibility and warning state. Structured info items can be aligned in various positions and can use a larger
  font if specified.
  
  ![Info Item Structured Example](images/info_item_api_structured_1.png)
  
  **Example:**
  ```
  import gom
  import gom.api.infoitem
  
  item_structured = gom.api.infoitem.create_structured('INFO_GENERAL', 'bottom')
  item_structured.set_heading(text="My Heading")
  item_structured.set_description("Description text")
  item_structured.add_single_shortcut(keys="ctrl+alt", mouse="left_button", description="Shortcut description")
  item_structured.show()
  ```
  '''

  def __init__ (self, instance_id):
    super ().__init__ (instance_id)
  
  def set_warning(self, state:bool) -> None:
    '''
    @brief Set the warning state for this structured info item
    
    Sets whether this info item should be displayed in a warning state. When set to true,
    the item will be visually highlighted as a warning in the user interface.
    
    ![Info Item Structured Example](images/info_item_api_structured_2.png)
    
    @param state If true, the item is marked as a warning; otherwise, it is shown normally.
    '''
    return self.__call_method__('set_warning', state)

  def set_always_visible(self, state:bool) -> None:
    '''
    @brief Set the always-visible state for this structured info item
    
    Sets whether this info item should always be visible, regardless of its priority or other conditions.
    When set to true, the item will remain visible in the user interface at all times.
    
    @param state If true, the item is always visible; otherwise, it follows normal visibility rules.
    '''
    return self.__call_method__('set_always_visible', state)

  def get_configuration(self) -> dict:
    '''
    @brief Return the current configuration of this structured info item as a dictionary
    
    This method returns the current configuration and state of the structured info item as a dictionary.
    The configuration includes properties such as category, alignment, font size, warning state,
    always-visible state, heading, description, and shortcuts. This is mainly intended for debugging or
    inspection purposes.
    
    @return Dictionary containing the configuration of the structured info item
    '''
    return self.__call_method__('get_configuration')

  def show(self) -> None:
    '''
    @brief Show this structured info item in the user interface
    
    Displays the structured info item in the application's graphical user interface using the current content.
    '''
    return self.__call_method__('show')

  def clear(self) -> None:
    '''
    @brief Clear the content and hide this structured info item
    
    Removes the content from the info item and hides it from the user interface.
    '''
    return self.__call_method__('clear')

  def set_heading(self, icon:str='', text:str='', help_id:str='') -> None:
    '''
    @brief Set the heading for this structured info item
    
    Sets the heading icon, text, and help id for the structured info item.
    
    The `icon` parameter supports multiple input formats
    - Internal icon identifier from GIcon::Cache
    - Complete AddOnUrl pointing to an icon file
    - Path to an external file
    - Base64-encoded QImage or QPixmap string
    
    **Examples:**
    ```python
    # Use an internal icon name
    item_structured.set_heading(icon="zui_holy_placeholder", text="My Heading")
    
    # Use an AddOnUrl
    icon = "acp:///<addon_uuid>/.../testicon.svg"
    item_structured.set_heading(icon=icon, text="My Heading")
    
    # Use an external file path
    icon = "C:/icons/myicon.png"
    item_structured.set_heading(icon=icon, text="My Heading")
    
    # Use a base64-encoded string
    icon = "iVBORw0KG....AAAAAK7QJANhcmnoAAAAAElFTkSuQmCC"
    item_structured.set_heading(icon=icon, text="My Heading")
    ```
    
    @param icon The icon to display in the heading
    @param text The heading text
    @param help_id The help id associated with the heading
    '''
    return self.__call_method__('set_heading', icon, text, help_id)

  def set_description(self, description:str) -> None:
    '''
    @brief Set the description for this structured info item
    
    Sets the description text for the structured info item.
    
    **Example:**
    ```
    item_structured.set_description("Description text")
    ```
    
    @param description The description text to display
    '''
    return self.__call_method__('set_description', description)

  def add_single_shortcut(self, keys:str='', mouse:str='', description:str='') -> None:
    '''
    @brief Add a single shortcut to this structured info item
    
    Adds a shortcut consisting of a key sequence and/or mouse button, with an optional description.
    
    The format and rules for the `keys` parameter are as follows:
    - It may consist of zero or more modifier keys (`Ctrl`, `Shift`, `Alt`) and at most one regular key.
    - For the complete list of keys, see the [Qt::Key enum documentation](https://doc.qt.io/qt-6/qt.html#Key-enum). Use
    the string after "Key_", e.g., `"Key_F1"` → `"F1"`, `"Key_A"` → `"A"`.
    - Modifiers and the regular key are combined with `+`, e.g., `"Ctrl+Alt+S"`.
    - Key names are case-insensitive.
    - You may specify only modifiers (e.g., `"Ctrl+Alt"`), or leave `keys` empty to use only a mouse button.
    
    The list of available mouse buttons can be obtained using <a
    href="#gom-api-infoitem-structured-get-mouse-buttons">`item_structured.get_mouse_buttons()`</a>.
    
    **Example:**
    ```
    item_structured.add_single_shortcut(keys="ctrl+alt", mouse="left_button", description="Single shortcut example")
    ```
    
    @param keys The key sequence
    @param mouse The mouse button
    @param description The description of the shortcut
    '''
    return self.__call_method__('add_single_shortcut', keys, mouse, description)

  def add_double_shortcut(self, keys1:str='', mouse1:str='', keys2:str='', mouse2:str='', description:str='') -> None:
    '''
    @brief Add a double shortcut to this structured info item
    
    Adds a shortcut consisting of two key sequence and/or mouse combinations, with an optional description.
    
    For detailed information about the format and rules for `keys1`, `keys2`, `mouse1`, and `mouse2`,
    see the documentation for <a href="#gom-api-infoitem-structured-add-single-shortcut">`add_single_shortcut`</a>.
    
    **Example:**
    ```
    item_structured.add_double_shortcut(keys1="ctrl", mouse1="left_button", keys2="shift", mouse2="right_button", description="Double shortcut example")
    ```
    
    @param keys1 The first key sequence
    @param mouse1 The first mouse button
    @param keys2 The second key sequence
    @param mouse2 The second mouse button
    @param description The description of the shortcut
    '''
    return self.__call_method__('add_double_shortcut', keys1, mouse1, keys2, mouse2, description)

  def get_mouse_buttons(self) -> list[str]:
    '''
    @brief Return the list of all available mouse buttons
    
    The structured info item supports the following mouse buttons: left_button, right_button, middle_button, and mouse_wheel.
    ![Info Item Structured Example](images/info_item_api_structured_3.png)
    
    **Example:**
    ```
    import gom
    import gom.api.infoitem
    
    item_structured = gom.api.infoitem.create_structured('INFO_GENERAL', 'bottom')
    print(item_structured.get_mouse_buttons())
    ```
    
    @return List of info category names as strings
    '''
    return self.__call_method__('get_mouse_buttons')


def get_categories() -> list[str]:
  '''
  @brief Return the list of all available info categories
  
  **Example:**
  ```
  import gom
  import gom.api.infoitem
  
  print(gom.api.infoitem.get_categories())
  ```
  
  @return List of info category names as strings
  '''
  return gom.__api__.__call_function__()

def get_alignments() -> list[str]:
  '''
  @brief Return the list of all available info alignments
  
  **Example:**
  ```
  import gom
  import gom.api.infoitem
  
  print(gom.api.infoitem.get_alignments())
  ```
  
  @return List of alignment names as strings
  '''
  return gom.__api__.__call_function__()

def create_text(category:str, alignment:str='', large_font:bool=False) -> Text:
  '''
  @brief Create a new text info item
  
  Creates and returns a new info item that displays plain text.
  
  **Example:**
  ```
  import gom
  import gom.api.infoitem
  
  item_text = gom.api.infoitem.create_text('INFO_WARNING', 'top_left')
  ```
  
  The list of available categories can be obtained using <a href="#gom-api-infoitem-get-categories">`gom.api.infoitem.get_categories`</a>,
  and the list of available alignments can be obtained using <a href="#gom-api-infoitem-get-alignments">`gom.api.infoitem.get_alignments`</a>.
  
  @param category The info category for the item (required)
  @param alignment The alignment for the item (optional, default: 'bottom')
  @param large_font Whether to use a large font (optional, default: False)
  @return The created text info item
  '''
  return gom.__api__.__call_function__(category, alignment, large_font)

def create_structured(category:str, alignment:str='', large_font:bool=False) -> Structured:
  '''
  @brief Create a new structured info item
  
  Creates and returns a new info item that displays structured content which can include a heading, description, and
  shortcuts.
  
  **Example:**
  ```
  import gom
  import gom.api.infoitem
  
  item_structured = gom.api.infoitem.create_structured('INFO_GENERAL', 'bottom')
  ```
  
  The list of available categories can be obtained using <a href="#gom-api-infoitem-get-categories">`gom.api.infoitem.get_categories`</a>,
  and the list of available alignments can be obtained using <a href="#gom-api-infoitem-get-alignments">`gom.api.infoitem.get_alignments`</a>.
  
  @param category The info category for the item (required)
  @param alignment The alignment for the item (optional, default: 'bottom')
  @param large_font Whether to use a large font (optional, default: False)
  @return The created structured info item
  '''
  return gom.__api__.__call_function__(category, alignment, large_font)

