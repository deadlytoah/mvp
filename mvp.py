# coding: utf-8
""" entry point of the application """

import sys
from PyQt5 import QtWidgets
from dataentry import DataEntryForm

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = DataEntryForm()
    window.gui.show()
    sys.exit(app.exec())
