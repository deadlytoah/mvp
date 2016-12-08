# coding: utf-8
"""Displays the flash card of the Bible verses."""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from screen import toggle_screen
from sdb import sdb
from simplelayout import SimpleLayout

TRANSLATION = 'nkjv'
DB_EXT = '.db'

window = None

class FlashCardForm(QtWidgets.QDialog):
    """form for entering new verses"""
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.gui = uic.loadUi("flashcard.ui")
        self.gui.action_enter_verses.triggered.connect(enter_verses)
        self.gui.action_debug_inspect_database.triggered.connect(debug_view_db)
        self.gui.action_debug_layout_engine.triggered.connect(debug_layout_engine)
        self.gui.lineedit_navigate_to.textEdited.connect(_navigate_to)

        self.canvas = FlashCardCanvas()
        self.gui.centralWidget().layout().addWidget(self.canvas)

        self.database = sdb.init(TRANSLATION + DB_EXT)
        records = sdb.read(self.database)

        if len([r for r in records if r['deleted'] == '0']) == 0:
            self.canvas.set_empty_database()
        else:
            self.canvas.set_title(records[0]['key'] + ' (' + TRANSLATION.upper() + ')')
            self.canvas.set_text(records[0]['text'])

        global window
        window = self

class FlashCardCanvas(QtWidgets.QWidget):
    def __init__(self):
        super(FlashCardCanvas, self).__init__()
        self.render = {
            'lines': [],
            'line_spacing': 20,
            'view_rect': None
        }

        self.EMPTY_LINE = {
            'font': QtGui.QFont('SansSerif', 12),
            'colour': QtGui.QColor('black'),
            'text': ''
        }

    def set_empty_database(self):
        self.set_title('Nothing in the database yet.')
        self.set_text('Please enter some verses first.')

    def set_title(self, title):
        title = {
            'font': QtGui.QFont('SansSerif', 20, QtGui.QFont.Black),
            'colour': QtGui.QColor('gray'),
            'text': title
        }

        lines = self.render['lines']
        if len(lines) == 0:
            lines.append(title)
        else:
            lines[0] = title

        if len(lines) == 1:
            lines.append(self.EMPTY_LINE)
        else:
            lines[1] = self.EMPTY_LINE

    def set_text(self, text):
        lines = self.render['lines']
        layout = SimpleLayout().layout(text)

        lines = lines[0:2]
        self.render['lines'] = lines
        while len(lines) < 2:
            lines.append(self.EMPTY_LINE)

        font = QtGui.QFont('SansSerif', 12)
        colour = QtGui.QColor('black')

        for text in layout:
            lines.append({
                'font': font,
                'colour': colour,
                'text': text
             })

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)

        self.render['view_rect'] = event.rect()

        qp.setPen(QtGui.QColor('black'))
        qp.setFont(QtGui.QFont('SansSerif', 12))

        lines = self.render['lines']
        middle = len(lines) / 2

        for i, line in enumerate(lines):
            self._render_line(qp, self.render, i - middle, line)

        qp.end()

    def _render_line(self, qp, render, offset, line):
        rect = render['view_rect']
        line_spacing = render['line_spacing']
        font = line['font']
        colour = line['colour']
        text = line['text']

        rect.moveTop(offset * line_spacing)
        qp.setPen(colour)
        qp.setFont(font)
        qp.drawText(rect, QtCore.Qt.AlignCenter, text)

def enter_verses():
    """switch to the verse entry screen"""
    toggle_screen()

def debug_view_db():
    from dbgviewdb import DbgViewDb
    DbgViewDb().gui.show()

def debug_layout_engine():
    from dbglayout import DbgLayout
    from simplelayout import SimpleLayout
    dbglayout = DbgLayout(window)
    dbglayout.set_text('Paul and Timothy, bondservants of Jesus Christ, To all the saints in Christ Jesus who are in Philippi, with the bishops and deacons:')
    dbglayout.add_layout_engine(SimpleLayout())
    dbglayout.show()

def _navigate_to():
    dest = window.gui.lineedit_navigate_to.text()
    split = dest.split(' ', 1)
    book = split[0]
    if len(split) > 1:
        split = split[1].split(':', 1)
        chapter = split[0].strip()
        if len(split) > 1:
            verse = split[1].strip()
        else:
            verse = ''
    else:
        chapter = ''
        verse = ''

    records = sdb.read(window.database)
    matches = [r for r in records if r['key'].lower().startswith(book.lower()) if chapter == '' or r['key'].split(' ', 1)[1].split(':')[0] == chapter if verse == '' or r['key'].split(':', 1)[1] == verse]

    if len(matches) > 0:
        window.canvas.set_title(matches[0]['key'])
        window.canvas.set_text(matches[0]['text'])
    else:
        window.canvas.set_title('No Matches')
        window.canvas.set_text('Please enter a valid book abbreviation followed by chapter number.')

    window.canvas.update()
