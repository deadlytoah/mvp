# coding: utf-8
"""Provides GUI for the data entry screen."""

import re
from PyQt5 import QtWidgets
from PyQt5 import uic
from sdb import sdb
from screen import toggle_screen

TRANSLATION = 'nkjv'
DB_EXT = '.db'

window = None

class DataEntryForm:
    """form for entering new verses"""
    def __init__(self):
        self.gui = uic.loadUi("dataentry.ui")
        self.gui.button_enter.clicked.connect(enter_verses)
        self.gui.action_scrub.triggered.connect(menu_scrub)
        self.gui.action_view_flash_cards.triggered.connect(view_flash_cards)
        self.gui.action_debug_inspect_database.triggered.connect(debug_view_db)
        self.gui.action_debug_layout_engine.triggered.connect(debug_layout_engine)
        self.gui.action_display_graph.triggered.connect(debug_display_graph)

        global window
        window = self

def enter_verses():
    """action for the enter push button. enters verses into the database

    """
    database = sdb.init(TRANSLATION + DB_EXT)
    key = window.gui.lineedit_book.text().strip() + ' ' + \
          window.gui.lineedit_chapter.text().strip() + ':'
    input_text = window.gui.textedit_verses.toPlainText()

    for line in input_text.splitlines():
        line = line.strip()
        if len(line) > 0:
            verse, text = line.split(' ', 1)
            record = {
                'key': key + verse,
                'text': text
            }
            sdb.append(database, record)

def menu_scrub():
    """action for the scrub menu item"""
    textedit = window.gui.textedit_verses
    input_text = textedit.toPlainText()

    info = {}
    input_text = _scrub_book_and_chapter(info, input_text)
    input_text = _scrub_verses(info, input_text)

    textedit.setPlainText(input_text)
    window.gui.lineedit_book.setText(info["book"])
    window.gui.lineedit_chapter.setText(info["chapter"])
    window.gui.lineedit_verses.setText(info["verses"])

def _scrub_book_and_chapter(info, text):
    obj, text = text.split(']', 1)
    _, obj = obj.split('[', 1)
    book, chapter_verses, _ = obj.split(' ', 2)
    chapter, verses = chapter_verses.split(':', 1)

    info["book"] = book
    info["chapter"] = chapter
    info["verses"] = verses
    return text.strip()

def _scrub_verses(info, text):
    start = info["verses"].split('-', 1)[0]
    array = re.split('[0-9]', text.strip())
    array = [x for x in array if len(x.strip()) > 0]
    verse_index = int(start)

    for i, e in enumerate(array):
        array[i] = str(verse_index) + ' ' + array[i].strip()
        verse_index += 1

    return '\n'.join(array)

def view_flash_cards():
    """switch to the flash cards screen"""
    toggle_screen()

def debug_view_db():
    from dbgviewdb import DbgViewDb
    DbgViewDb().gui.show()

def debug_layout_engine():
    from dbglayout import DbgLayout
    from simplelayout import SimpleLayout
    from graphlayout import GraphLayout
    dbglayout = DbgLayout(window.gui)
    dbglayout.set_text('Paul and Timothy, bondservants of Jesus Christ, To all the saints in Christ Jesus who are in Philippi, with the bishops and deacons:')
    dbglayout.add_layout_engine(SimpleLayout())
    dbglayout.add_layout_engine(GraphLayout())
    dbglayout.show()

def debug_display_graph():
    from dbggraph import DbgGraph
    dbggraph = DbgGraph()
    dbggraph.set_text('Paul and Timothy, bondservants of Jesus Christ, To all the saints in Christ Jesus who are in Philippi, with the bishops and deacons:')
    dbggraph.gui.show()
