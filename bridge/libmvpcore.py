# coding: utf-8
"""Is a bridge to the backend"""

from ctypes import POINTER
import ctypes

""" The name of the shared library to load, which must be found in one
of the directories in LD_LIBRARY_PATH environment variable. """
LIB_NAME = "libmvpcore.dylib"

"""Data structure defining functions and types of their
arguments."""
EXTFNS = [["session_new", [ctypes.c_char_p], ctypes.c_void_p],
          ["session_destroy", [ctypes.c_void_p], None],
          ["session_write", [ctypes.c_void_p], ctypes.c_int],
          ["session_delete", [ctypes.c_void_p], ctypes.c_int],
          ["session_set_range", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int],
          ["session_set_level", [ctypes.c_void_p, ctypes.c_int], ctypes.c_int],
          ["session_set_strategy", [ctypes.c_void_p, ctypes.c_int], ctypes.c_int],
          ["session_list_sessions", [ctypes.c_char_p, POINTER(ctypes.c_size_t)], ctypes.c_int],
          ["session_get_message", [ctypes.c_int], ctypes.c_char_p]]

class Libmvpcore:
    """ Helps invoking functions exported by libmvpcore. """

    def __init__(self):
        """ Loads libmvpcore and sets up functions exported by it. """
        self.library = ctypes.CDLL(LIB_NAME)

        # Set up each external function exported by libste.
        for entry in EXTFNS:
            func = getattr(self.library, entry[0])
            func.argtypes = entry[1]
            if entry[2] is not None:
                func.restype = entry[2]

            setattr(self, entry[0], func)

libmvpcore = Libmvpcore()
