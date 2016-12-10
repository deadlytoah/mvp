# coding: utf-8
""" entry point of the application """

import sys
from PyQt5 import QtWidgets
from screen import init_screens
from dataentry import DataEntryForm
from flashcard import FlashCardForm

FORM_TYPES = [FlashCardForm, DataEntryForm]

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    init_screens(FORM_TYPES)
    sys.exit(app.exec())
