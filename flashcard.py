# coding: utf-8
"""Displays the flash card of the Bible verses."""

from PyQt5 import QtWidgets
from PyQt5 import uic
from screen import toggle_screen

window = None

class FlashCardForm(QtWidgets.QDialog):
    """form for entering new verses"""
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.gui = uic.loadUi("flashcard.ui")
        self.gui.action_enter_verses.triggered.connect(enter_verses)

        global window
        window = self

def enter_verses():
    """switch to the verse entry screen"""
    toggle_screen()
