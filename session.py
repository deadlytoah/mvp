# coding: utf-8
"""Acts as a bridge between the GUI and the session backend."""

from enum import Enum
from libmvpcore import libmvpcore
import ctypes

######################################################################
# Error Code and Types
######################################################################

class ErrorKind(Enum):
    OK = 0
    IOError = 1
    SessionExists = 2
    SessionCorruptData = 3
    SessionBufferTooSmall = 4
    RangeParseError = 5
    LevelUnknown = 6
    StrategyUnknown = 7

class Error(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class IOError(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

class SessionExists(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

class SessionCorruptData(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

class SessionBufferTooSmall(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

class RangeParseError(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

class LevelUnknown(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

class StrategyUnknown(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

_error_switcher = {
    ErrorKind.IOError: IOError,
    ErrorKind.SessionExists: SessionExists,
    ErrorKind.SessionCorruptData: SessionCorruptData,
    ErrorKind.SessionBufferTooSmall: SessionBufferTooSmall,
    ErrorKind.RangeParseError: RangeParseError,
    ErrorKind.LevelUnknown: LevelUnknown,
    ErrorKind.StrategyUnknown: StrategyUnknown,
}

def _map_error(errorkind):
    return _error_switcher.get(errorkind, Error)

######################################################################
# Data Structures
######################################################################

class Location(ctypes.Structure):
    """creates a struct to point to a location in the Bible"""

    _fields_ = [('translation', ctypes.c_ubyte * 8),
                ('book', ctypes.c_ubyte * 8),
                ('chapter', ctypes.c_short),
                ('sentence', ctypes.c_short),
                ('verse', ctypes.c_short)]

class Session:
    def __init__(self, name):
        """Initialises a new Session.

        The new Session instance is not persisted in disk until
        write() method is called.

        """
        self.handle = libmvpcore.session_new(ctypes.bytes(name, encoding='utf8'))

    def __del__(self):
        libmvpcore.session_destroy(self.handle)

    def write(self):
        res = libmvpcore.session_write(self.handle)
        if res != 0:
            raise _map_error(res)(get_message(res).value)

    def delete(self):
        res = libmvpcore.session_delete(self.handle)
        if res != 0:
            raise _map_error(res)(get_message(res).value)
        else:
            self.handle = None

    def set_range(self, start, end):
        res = libmvpcore.session_set_range(self.handle, start, end)
        if res != 0:
            raise _map_error(res)(get_message(res).value)

    def set_level(self, level):
        res = libmvpcore.session_set_level(self.handle, level)
        if res != 0:
            raise _map_error(res)(get_message(res).value)

    def set_strategy(self, strategy):
        res = libmvpcore.session_set_strategy(self.handle, strategy)
        if res != 0:
            raise _map_error(res)(get_message(res).value)

def list_sessions():
    pass

def get_message(error_code):
    libmvpcore.session_get_message(error_code)
