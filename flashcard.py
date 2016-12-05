# coding: utf-8
"""Displays the flash card of the Bible verses."""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from screen import toggle_screen

window = None

class FlashCardForm(QtWidgets.QDialog):
    """form for entering new verses"""
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.gui = uic.loadUi("flashcard.ui")
        self.gui.action_enter_verses.triggered.connect(enter_verses)
        self.gui.action_debug_inspect_database.triggered.connect(debug_view_db)
        self.gui.action_debug_layout_engine.triggered.connect(debug_layout_engine)

        self.canvas = FlashCardCanvas()
        self.gui.setCentralWidget(self.canvas)

        global window
        window = self

class FlashCardCanvas(QtWidgets.QWidget):
    def __init__(self):
        super(FlashCardCanvas, self).__init__()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        self._warn_empty_database(qp, event)
        qp.end()

    def _warn_empty_database(self, qp, event):
        title = 'Nothing in the database yet.'
        message = 'Please enter some verses first.'

        qp.setPen(QtGui.QColor('black'))
        qp.setFont(QtGui.QFont('Serif', 20, QtGui.QFont.Black))
        rect = event.rect()
        rect.moveTop(-30)
        qp.drawText(rect, QtCore.Qt.AlignCenter, title)
        qp.setPen(QtGui.QColor('gray'))
        qp.setFont(QtGui.QFont('Serif', 12))
        qp.drawText(event.rect(), QtCore.Qt.AlignCenter, message)

def enter_verses():
    """switch to the verse entry screen"""
    toggle_screen()

def debug_view_db():
    from dbgviewdb import DbgViewDb
    DbgViewDb().gui.show()

def debug_layout_engine():
    from dbglayout import DbgLayout
    DbgLayout(window).show()
