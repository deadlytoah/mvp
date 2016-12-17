# coding: utf-8
"""Inspect the contents of the database."""

from PyQt5 import uic

window = None

class DbgSentences():
    """form for entering new verses"""
    def __init__(self):
        self.gui = uic.loadUi('debug-sentences.ui')

        global window
        window = self
