from ctypes import *
from bridge.libmvpcore import libmvpcore
import ctypes

class Character(ctypes.Structure):
    """Represents a character in a Bible verse."""
    _fields_ = [('id', c_size_t),
                ('character', c_uint32),
                ('whitespace', c_uint32), # boolean
                ('newline', c_uint32), # boolean
                ('has_word', c_uint32), # boolean
                ('word', c_size_t),
                ('visible', c_uint32), # boolean
                ('has_typed', c_uint32), # boolean
                ('typed', c_uint32),
                ('correct', c_uint32), # boolean
    ]

class Word(ctypes.Structure):
    """Represents a word in a Bible verse."""
    _fields_ = [('id', c_size_t),
                ('word', c_char_p),
                ('visible', c_uint32), # boolean
                ('touched', c_uint32), # boolean
                ('behind', c_uint32), # boolean
                ('characters_len', c_size_t),
                ('characters_ptr', POINTER(c_size_t)),
    ]

class Sentence(ctypes.Structure):
    """Represents a list of words that make up a sentence."""
    _fields_ = [('words_len', c_size_t),
                ('words_ptr', POINTER(c_size_t)),
    ]

class StateRaw(ctypes.Structure):
    """Represents the state of the speedtype app.

    This is the interface to the raw State structure.  The State class
    is a nice wrapper around it.

    """
    _fields_ = [('buffer_len', c_size_t),
                ('buffer_ptr', POINTER(Character)),
                ('words_len', c_size_t),
                ('words_ptr', POINTER(Word)),
                ('sentences_len', c_size_t),
                ('sentences_ptr', POINTER(Sentence)),
    ]

class SpeedtypeError(Exception):
    def __init__(self, code):
        self.code = code

class State:
    """Embodies the state and methods of the speedtype module."""
    def __init__(self):
        self._state = libmvpcore.speedtype_new()

    def __del__(self):
        libmvpcore.speedtype_delete(self._state)

    def process_line(self, line):
        retcode = libmvpcore.speedtype_process_line(
            self._state, bytes(line, 'utf8'))
        if retcode != 0:
            raise SpeedtypeError(retcode)

        self._enable_idiomatic_access()

    def get_state(self):
        return ctypes.cast(self._state, POINTER(StateRaw)).contents

    def _enable_idiomatic_access(self):
        """Enables idiomatic access of the data structures.

        Converts the ctypes structures into Python dictionaries that
        can be idiomatically accessed and serialised.

        The resulting structures contain native Python boolean types
        as opposed to unsigned integers representing C booleans.
        Optional types become Python variables containing either None
        or a valid value.

        """
        state = self.get_state()

        buf = []
        for i in range(0, state.buffer_len):
            word = None
            if state.buffer_ptr[i].has_word != 0:
                word = state.buffer_ptr[i].word
            typed = None
            if state.buffer_ptr[i].has_typed != 0:
                typed = state.buffer_ptr[i].typed

            char = {}
            char['id'] = state.buffer_ptr[i].id
            char['char'] = chr(state.buffer_ptr[i].character)
            char['whitespace'] = state.buffer_ptr[i].whitespace != 0
            char['newline'] = state.buffer_ptr[i].newline != 0
            char['word'] = word
            char['visible'] = state.buffer_ptr[i].visible != 0
            char['typed'] = typed
            char['correct'] = state.buffer_ptr[i].correct != 0
            buf.append(char)
        self._buf = buf

        words = []
        for i in range(0, state.words_len):
            characters_len = state.words_ptr[i].characters_len
            characters_ptr = state.words_ptr[i].characters_ptr
            characters = []
            for j in range(0, characters_len):
                characters.append(characters_ptr[j])

            word = {}
            word['id'] = state.words_ptr[i].id
            word['word'] = state.words_ptr[i].word.decode()
            word['visible'] = state.words_ptr[i].visible != 0
            word['touched'] = state.words_ptr[i].touched != 0
            word['behind'] = state.words_ptr[i].behind != 0
            word['characters'] = characters

            words.append(word)
        self._words = words

        sentences = []
        for i in range(0, state.sentences_len):
            words_len = state.sentences_ptr[i].words_len
            words_ptr = state.sentences_ptr[i].words_ptr
            words = []
            for j in range(0, words_len):
                words.append(words_ptr[j])
            sentences.append(words)
        self._sentences = sentences

    def buf(self):
        return self._buf

    def words(self):
        return self._words

    def sentences(self):
        return self._sentences

    def set_buf(self, buf):
        self._buf = buf

    def set_words(self, words):
        self._words = words

    def set_sentences(self, sentences):
        self._sentences = sentences
