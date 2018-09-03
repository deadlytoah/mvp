# coding: utf-8
"""a config module that contains attributes that are shared by all the
modules in the application.

"""

DB_EXT = '.sdb'
COLOURS = {
    'background': 'white',
    'foreground': 'black',
    'title': 'lightgray',
    'guide': 'gray',
    'underscore': 'lightgray',
    'correct': 'black',
    'incorrect': 'red',
    'caret': 'black',
}
DEFAULT_TRANSLATION='esv'
FONT_FAMILY = 'Menlo'
PERSIST_INTERVAL = 300
SENTENCE_DELIMITERS = '.:;?!'
WORD_DELIMITERS = ' .,:;?!'

translation=DEFAULT_TRANSLATION
