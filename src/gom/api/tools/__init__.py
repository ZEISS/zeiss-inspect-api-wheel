#
# API declarations for gom.api.tools
#
# @brief General scripting tools
#
'''
@brief API providing a general set of scripting tools

This API contains a collection of tools that are useful for scripting purposes.
'''

import gom
import gom.api.interpreter


class MultiElementCreationScope:
    '''
    @brief Context manager for creating multiple elements in a single step

    This class can be used in a `with` statement to prohibid the full application synchronization step
    between commands. Usually, the ZEISS INSPECT software synchronizes the application after each
    command being executed. This can be very time consuming, if a large number of elements are created
    in a single step. By using this scope, the synchronization is only done once after all elements
    have been created, as soon as this scope is left.

    ```{caution}
    Disabling the full application synchronization can lead to various side effects, so use this with caution !
    Also, the UI update will be locked during the time the scope is active. So the user will not see any changes 
    in the UI until the scope is left again.
    ```

    **Example**

    ```
    import gom.api.tools

    with gom.api.tools.MultiElementCreationScope():
        for _ in range(10000):
            # Will not lead to a full application synchronization
            gom.script.inspection.create_some_simple_point(...)

    # Full application synchronization is done here, we are safe again

    gom.script.inspection.create_some_complex_element_based_on_these_points (...)
    ```

    '''

    def __init__(self):
        pass

    def __enter__(self):
        gom.api.interpreter.__enter_multi_element_creation_scope__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        gom.api.interpreter.__exit_multi_element_creation_scope__()
