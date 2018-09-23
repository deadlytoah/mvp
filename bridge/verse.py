from bridge.libmvpcore import libmvpcore
import ctypes

class Verse(ctypes.Structure):
    """Represents a verse in the Bible."""
    _fields_ = [('key', ctypes.c_ubyte * 16),
                ('text', ctypes.c_ubyte * 256)]

class VerseView(ctypes.Structure):
    """Represents a view of one or more verses in the Bible."""
    _fields_ = [('count', ctypes.c_size_t),
                ('verses', Verse * 176)]

def find_all(translation):
    """Invokes verse_find_all() function in the libmvpcore."""
    view = VerseView()
    ret = libmvpcore.verse_find_all(ctypes.c_char_p(bytes(translation, 'utf8')),
                                    ctypes.byref(view))
    records = []
    if ret == 0:
        for i in range(0, view.count):
            verse = view.verses[i]
            key = ctypes.c_char_p(ctypes.addressof(verse.key)).value.decode()
            text = ctypes.c_char_p(ctypes.addressof(verse.text)).value.decode()
            records.append({'key': key, 'text': text, 'deleted': '0'})
        return records
    else:
        return None

def find_by_book_and_chapter(translation, book, chapter):
    """Invokes verse_find_by_book_and_chapter() in the libmvpcore."""
    view = VerseView()
    ret = libmvpcore.verse_find_by_book_and_chapter(ctypes.c_char_p(bytes(translation, 'utf8')),
                                                    ctypes.byref(view),
                                                    ctypes.c_char_p(bytes(book, 'utf8')),
                                                    ctypes.c_short(chapter))
    records = []
    if ret == 0:
        for i in range(0, view.count):
            verse = view.verses[i]
            key = ctypes.c_char_p(ctypes.addressof(verse.key)).value.decode()
            text = ctypes.c_char_p(ctypes.addressof(verse.text)).value.decode()
            records.append({'key': key, 'text': text, 'deleted': '0'})
        return records
    else:
        return None
