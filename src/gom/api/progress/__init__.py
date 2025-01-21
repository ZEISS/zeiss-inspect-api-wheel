#
# API declarations for gom.api.progress
#
# @brief API for accessing the progress bar in the main window
#
# This API provides basic access to the progress bar in the main window
#
'''
@brief API for accessing the progress bar in the main window

This API provides basic access to the progress bar in the main window
'''


from gom.api.__internal__progress import _create_internal_progress_bar


class ProgressBar ():
    '''
    @brief Class representing the ProgressBar

    This class is meant to be used with the Python 'with' statement

    #### Example

    ```
    import gom.api.progress

    with gom.api.progress.ProgressBar() as bar:
        bar.set_message('Calculation in progress')
        for i in range(100):
            # Do some calculations
            foo()
            # Increase the progress
            bar.set_progress(i)    

    # Progress bar entry gets removed automatically after leaving the 'with' statement
    ```
    '''

    def __init__(self):
        # Create an internal gom-ProgressBar instance using a 'secret' passcode, which discourages direct creation from the enduser
        # The definition on the C++ side is found in "mpackage_progress_bar_api.cpp"
        self._progress_bar = _create_internal_progress_bar("safe_progress_bar_internal_create")

        self._message = ''
        self._progress = 0

        self._active = False  # Flag to reduce API calls, when it is known that the progress cannot be updated
        return

    def __enter__(self):
        # Only register the progressWatcher at the start of a scope
        self._progress_bar._register_watcher()
        self._active = True
        # Trigger initial message/progress if set before entering the scope
        if (len(self._message) > 0 or self._progress > 0):
            self._update()
        return self

    def __exit__(self, exctype: any, excinst: any, exctb: any) -> None:
        # Deregister the progressWatcher at the end of scope
        self._progress_bar._deregister_watcher()
        self._active = False
        return

    def _update(self) -> None:
        # Only call on the API if a watcher is known to be registered
        if (self._active):
            # Update the progress
            self._progress_bar._set_progress(self._progress)
            # Display the numerical progress behind the given message
            self._progress_bar._set_message(self._message + ' (' + str(self._progress) + ')')
        return

    def set_progress(self, progress: int) -> None:
        '''
        @brief Sets the progress in the main window progress bar
        @version 1

        @param progress in percent, given as an integer from 0 to 100
        @return nothing
        '''
        # Limit progress to the accepted range to avoid errors
        self._progress = progress
        if (self._progress < 0):
            self._progress = 0
        if (self._progress > 100):
            self._progress = 100

        self._update()
        return

    def set_message(self, message: str) -> None:
        '''
        @brief Sets a message in the main window progress bar
        @version 1

        @param message the message to display
        @return nothing
        '''
        self._message = message
        self._update()
        return

    def finish_progress(self) -> None:
        '''
        @brief Finishes the progress and removes this from the progress bar
        @version 1

        This object CANNOT be used for further progress reporting after calling this method

        Can be used if the progress bar should disappear but the with statement cannot be left yet

        @return nothing
        '''
        self._progress_bar._deregister_watcher()
        self._active = False
        return
