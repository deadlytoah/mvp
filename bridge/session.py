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
    Utf8Error = 8
    BookUnknown = 9
    StringConvertError = 10
    NulError = 11

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

class Utf8Error(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

class BookUnknown(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

class StringConvertError(Error):
    def __init__(self, msg):
        Error.__init__(self, msg)

class NulError(Error):
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
    ErrorKind.Utf8Error: Utf8Error,
    ErrorKind.BookUnknown: BookUnknown,
    ErrorKind.StringConvertError: StringConvertError,
    ErrorKind.NulError: NulError,
}

def _map_error(errorkind):
    return _error_switcher.get(errorkind, Error)

######################################################################
# Data Structures
######################################################################

class Session(ctypes.Structure):
    """Represents a speed typing session.

    The order of the fields and their types must match the
    corresponding data structure in the core library.

    """
    _fields_ = [('name', ctypes.c_ubyte * 64),
                ('range', Location * 2),
                ('level', ctypes.c_ubyte),
                ('strategy', ctypes.c_ubyte)]

class Location(ctypes.Structure):
    """creates a struct to point to a location in the Bible

    The order of the fields and their types must match the
    corresponding data structure in the core library.

    """
    _fields_ = [('translation', ctypes.c_ubyte * 8),
                ('book', ctypes.c_ubyte * 8),
                ('chapter', ctypes.c_short),
                ('sentence', ctypes.c_short),
                ('verse', ctypes.c_short)]

def list_sessions():
    pass

def get_message(error_code):
    libmvpcore.session_get_message(error_code)
