# coding: utf-8
"""Inspect the contents of the database."""

import json
from PyQt5 import uic
from sdb import Sdb

TRANSLATION = 'nkjv'
DB_EXT = '.sdb'

window = None

class DbgViewDb():
    """form for entering new verses"""
    def __init__(self):
        self.gui = uic.loadUi('debug-view-database.ui')

        global window
        window = self

        with Sdb(TRANSLATION + DB_EXT) as database:
            self.verse_table = [table for table in database.get_tables()
                            if table.name() == 'verse'][0]
            self.verse_table.create_manager()
            self.verse_table.verify()
            self.verse_table.service()
            records = self.verse_table.select_all()

        window.gui.textedit_database.setPlainText(json.dumps(records, indent = 4))
