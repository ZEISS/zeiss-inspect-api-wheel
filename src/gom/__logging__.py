#
# __logging__.py - Network related classes for connecting with the C++ application part
#
# (C) 2025 Carl Zeiss GOM Metrology GmbH
#
# Use of this source code and binary forms of it, without modification, is permitted provided that
# the following conditions are met:
#
# 1. Redistribution of this source code or binary forms of this with or without any modifications is
#    not allowed without specific prior written permission by GOM.
#
# As this source code is provided as glue logic for connecting the Python interpreter to the commands of
# the GOM software any modification to this sources will not make sense and would affect a suitable functioning
# and therefore shall be avoided, so consequently the redistribution of this source with or without any
# modification in source or binary form is not permitted as it would lead to malfunctions of GOM Software.
#
# 2. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or
#    promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import enum
import inspect
import logging
import os
import uuid

from datetime import datetime, timezone


def get_default_log_dir():
    """
    Determines and creates the default directory for log files based on the operating system and user privileges.

    On Windows, it uses the %ProgramData%\gom\log directory (defaulting to C:\ProgramData\gom\log if the environment variable is missing).
    On POSIX systems, it uses /var/log/gom if running as root, or ~/.local/share/gom/log for non-root users.

    Returns:
        str: The absolute path to the default log directory.
    """
    if os.name == "nt":
        # On Windows, get %ProgramData% (typically C:\ProgramData)
        program_data = os.environ.get("ProgramData")
        if not program_data:
            # Fallback if environment variable is missing
            program_data = r"C:\ProgramData"
        log_dir = os.path.join(program_data, "gom", "log")
    else:
        # On POSIX, use /var/log/gom or ~/.local/share/gom/log if not root
        if os.geteuid() == 0:
            log_dir = "/var/log/gom"
        else:
            log_dir = os.path.expanduser("~/.local/share/gom/log")

    os.makedirs(log_dir, exist_ok=True)

    return log_dir


class MillisecondFormatter(logging.Formatter):
    """
    A custom logging.Formatter that formats log record timestamps with millisecond precision.

    Overrides the formatTime method to allow formatting of timestamps with milliseconds.
    If a date format string (datefmt) is provided and contains '%f', it will be replaced
    with the milliseconds component (first three digits of microseconds) of the timestamp.

    Args:
        record (logging.LogRecord): The log record whose creation time is to be formatted.
        datefmt (str, optional): A date format string. If provided and contains '%f', it will
            be replaced with milliseconds.

    Returns:
        str: The formatted time string with millisecond precision.
    """

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            s = dt.strftime(datefmt)
            # Replace %f with milliseconds (first 3 digits of microseconds)
            s = s.replace('%f', f"{dt.microsecond // 1000:03d}")
            return s
        return super().formatTime(record, datefmt)


class ProtocolLogger:
    """
    ProtocolLogger is a logging utility designed to record protocol-related events in a structured log file, matching the format and domain conventions of a corresponding C++ logging system.

    Attributes:
        domain (str): The logging domain, set to 'scripting.core.protocol' to match the C++ domain.

    Classes:
        EventType (enum.Enum): Enumeration of protocol event types, including CONNECTED, DISCONNECTED, REQUEST, RESPONSE, and ERROR.

    Methods:
        __init__(log_dir=None):
            Initializes the ProtocolLogger instance.
            Determines the log directory (uses a default if not provided), constructs a log file name with a UTC timestamp and process ID, and sets up a file handler with a custom formatter for millisecond precision and ISO 8601 timestamps.

        log(event_type, event_id, message):
            Logs a protocol event with the specified type, identifier, and message.
            Automatically includes the caller's filename and line number, formats the timestamp to match C++ conventions, and records the thread ID.
            Supports event_id as a UUID or string.
    """

    domain = 'scripting.core.protocol'  # Must match the C++ domain

    class EventType(enum.Enum):
        """
        Enumeration of possible event types for logging purposes.

        Attributes:
            CONNECTED (str): Indicates a successful connection event.
            DISCONNECTED (str): Indicates a disconnection event.
            REQUEST (str): Represents a request event.
            RESPONSE (str): Represents a response event.
            ERROR (str): Represents an error event.
        """
        CONNECTED = "Connected"
        DISCONNECTED = "Disconnected"
        REQUEST = "Request"
        RESPONSE = "Response"
        ERROR = "Error"

    def __init__(self, log_dir=None):

        # Determine log directory
        if log_dir is None:
            log_dir = get_default_log_dir()

        # Compute log file name with start timestamp and process id
        start_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        pid = os.getpid()
        log_filename = f"python_{start_time}_{pid}.log"
        log_path = os.path.join(log_dir, log_filename)

        self.logger = logging.getLogger(ProtocolLogger.domain)
        handler = logging.FileHandler(log_path, encoding="utf-8")
        formatter = MillisecondFormatter(
            '%(asctime)s TID%(thread)d INFO  [%(name)s] %(event_type)s %(event_id)s %(message)s (%(filename)s:%(lineno)d)',
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        handler.setFormatter(formatter)
        self.logger.handlers = []
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        self.log_path = log_path

    def log(self, event_type, event_id, message):

        if isinstance(event_id, uuid.UUID):
            event_id = str(event_id)

        # Get caller's filename and line number from the call stack
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)
        if len(outer_frames) > 1:
            caller_frame = outer_frames[1]
            filename = os.path.basename(caller_frame.filename)
            lineno = caller_frame.lineno
        else:
            filename = "unknown"
            lineno = 0
        extra = {
            'event_type': event_type.value if isinstance(event_type, enum.Enum) else str(event_type),
            'event_id': event_id
        }

        # Patch asctime to match C++ format (ISO 8601 with ms, Z)
        record = self.logger.makeRecord(
            self.logger.name, logging.INFO, filename, lineno,
            message, (), None, None, extra)
        record.asctime = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        try:
            import threading
            record.thread = threading.get_ident()
        except ImportError:
            record.thread = 1
        record.event_type = event_type
        record.event_id = event_id
        record.filename = filename
        record.lineno = lineno
        record.name = self.logger.name
        self.logger.handle(record)


# Example usage:
if __name__ == "__main__":
    logger = ProtocolLogger()
    logger.log(ProtocolLogger.EventType.REQUEST.value, uuid.uuid4(), "Register")
    print(f"Log written to: {logger.log_path}")
