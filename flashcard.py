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

        global window
        window = self

        self.jump_to_dialog = uic.loadUi('jump-to.ui')
        self.jump_to_dialog.lineedit_jump_to.textEdited.connect(_peek)
        self.jump_to_dialog.accepted.connect(_accept_jump)
        self.jump_to_dialog.rejected.connect(_reject_jump)
        self.jump_to_dialog.move(0, 0)

        self.gui = uic.loadUi("flashcard.ui")
        self.gui.action_enter_verses.triggered.connect(enter_verses)
        self.gui.action_debug_inspect_database.triggered.connect(debug_view_db)
        self.gui.action_debug_layout_engine.triggered.connect(debug_layout_engine)
        self.gui.action_jump_to.triggered.connect(_prepare_jump)

        self.canvas = FlashCardCanvas()
        self.gui.setCentralWidget(self.canvas)

        self.database = sdb.init(TRANSLATION + DB_EXT)
        records = sdb.read(self.database)

        if len([r for r in records if r['deleted'] == '0']) == 0:
            self.dispkey = None
            self.canvas.set_empty_database()
        else:
            self.dispkey = records[0]['key']
            _display_with_key(self.dispkey)

        # Jump Stack is used for quickly bookmarking and switching to
        # previous locations between input sessions
        self.jump_stack = []

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

def _peek():
    dest = window.jump_to_dialog.lineedit_jump_to.text()
    split = dest.split(' ', 1)
    book = split[0]
    if len(split) > 1 and len(split[1]) > 0:
        split = split[1].split(':', 1)
        chapter = split[0]
        if len(split) > 1 and len(split[1]) > 0:
            verse = split[1]
        else:
            verse = '1'
    else:
        chapter = '1'
        verse = '1'

    records = sdb.read(window.database)
    matches = [rec for rec in records if rec['key'].lower().startswith(book.lower()) if rec['key'].split(' ', 1)[1] == '{0}:{1}'.format(chapter, verse)]

    if len(matches) > 0:
        window.jump_to_dialog.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        window.dispkey = matches[0]['key']
        window.canvas.set_title('Peeking at: ' + window.dispkey + ' (' + TRANSLATION.upper() + ') (enter – jump, esc – cancel)')
        window.canvas.set_text(matches[0]['text'])
    else:
        window.jump_to_dialog.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        window.dispkey = None
        window.canvas.set_title('No Matches')
        window.canvas.set_text('Please enter a valid book abbreviation followed by chapter number.')

    window.canvas.update()

def _display_with_key(key):
    records = sdb.read(window.database)
    matches = [rec for rec in records if rec['key'] == key]
    assert(len(matches) == 1)
    match = matches[0]
    window.canvas.set_title(match['key'] + ' (' + TRANSLATION.upper() + ')')
    window.canvas.set_text(match['text'])

def _accept_jump():
    _ = window.jump_stack.pop()
    assert(window.dispkey != None)
    _display_with_key(window.dispkey)
    window.jump_to_dialog.lineedit_jump_to.clear()

def _reject_jump():
    window.dispkey = window.jump_stack.pop()
    assert(window.dispkey != None)
    _display_with_key(window.dispkey)
    window.jump_to_dialog.lineedit_jump_to.clear()

def _prepare_jump():
    if window.dispkey != None:
        window.jump_stack.append(window.dispkey)
        window.jump_to_dialog.show()
    else:
        QtWidgets.QMessageBox.warning(window, 'mvp – Jump to', 'Unable to jump right now.')
