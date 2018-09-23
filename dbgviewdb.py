# coding: utf-8
"""Inspect the contents of the database."""

import config
import json
import model
from PyQt5 import uic

window = None

class DbgViewDb():
    """form for entering new verses"""
    def __init__(self):
        self.gui = uic.loadUi('debug-view-database.ui')

        global window
        window = self

        records = model.verse.find_all()
        window.gui.textedit_database.setPlainText(json.dumps(records, indent = 4))
