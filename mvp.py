# coding: utf-8
""" entry point of the application """

import argparse
import config
import sys
from PyQt5 import QtWidgets
from screen import init_screens

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Help memorising Bible verses.')
    parser.add_argument('-T', '--translation', nargs=1,
                        default=[config.DEFAULT_TRANSLATION],
                        help='name of the translation to work on')
    opts = parser.parse_args()
    config.translation = opts.translation[0]

    app = QtWidgets.QApplication(sys.argv)
    init_screens()
    sys.exit(app.exec())
