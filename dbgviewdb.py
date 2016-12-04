# coding: utf-8
"""Inspect the contents of the database."""

import json
from PyQt5 import uic
from sdb import sdb

TRANSLATION = 'nkjv'
DB_EXT = '.db'

window = None

class DbgViewDb():
    """form for entering new verses"""
    def __init__(self):
        self.gui = uic.loadUi('debug-view-database.ui')

        global window
        window = self

        database = sdb.init(TRANSLATION + DB_EXT)
        records = sdb.read(database)

        window.gui.textedit_database.setPlainText(json.dumps(records, indent = 4))
