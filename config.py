# coding: utf-8
"""a config module that contains attributes that are shared by all the
modules in the application.

"""

from PyQt5 import Qt, QtGui

DB_EXT = '.sdb'
COLOURS = {
    'background': QtGui.QColor(Qt.Qt.white),
    'foreground': QtGui.QColor(Qt.Qt.black),
    'title': QtGui.QColor(Qt.Qt.lightGray)
}
DEFAULT_TRANSLATION='esv'
FONT_FAMILY = 'Helvetica Neue'
SENTENCE_DELIMITERS = '.:;?!'

translation=DEFAULT_TRANSLATION
