# coding: utf-8
"""Displays the flash card of the Bible verses."""

import config
from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from PyQt5 import uic
from address import Address
from key import Key
from screen import toggle_screen
from sdb import Sdb
from graphlayout import GraphLayout

DB_EXT = '.sdb'
FONT_FAMILY = 'Helvetica Neue'
SENTENCE_DELIMITERS = '.:;?!'
COLOURS = {
    'background': QtGui.QColor(Qt.Qt.white),
    'foreground': QtGui.QColor(Qt.Qt.black),
    'title': QtGui.QColor(Qt.Qt.lightGray)
}

window = None

class FlashCardForm:
    """form for entering new verses"""
    def __init__(self):
        global window
        window = self

        self.jump_to_dialog = uic.loadUi('jump-to.ui')
        self.jump_to_dialog.lineedit_jump_to.textEdited.connect(_peek)
        self.jump_to_dialog.finished.connect(_conclude_jump)
        self.jump_to_dialog.move(0, 0)

        self.gui = uic.loadUi("flashcard.ui")
        self.gui.action_enter_verses.triggered.connect(enter_verses)
        self.gui.action_debug_inspect_database.triggered.connect(debug_view_db)
        self.gui.action_debug_layout_engine.triggered.connect(debug_layout_engine)
        self.gui.action_debug_sentences.triggered.connect(debug_sentences)
        self.gui.action_display_graph.triggered.connect(debug_display_graph)
        self.gui.action_jump_to.triggered.connect(_prepare_jump)

        self.canvas = FlashCardCanvas(GraphLayout())
        self.gui.setCentralWidget(self.canvas)
        self.canvas.setFocus(True)

        self.database = Sdb(config.translation + DB_EXT).__enter__()
        self.verse_table = [table for table in self.database.get_tables()
                            if table.name() == 'verse'][0]
        self.verse_table.create_manager()
        self.verse_table.verify()
        self.verse_table.service()
        records = self.verse_table.select_all()

        # Stack is used to help implementing input session.  The top
        # of the stack contains the currently display flash card, and
        # the very bottom is what we will revert to if the input
        # session fails.
        self.stack = []

        if len([r for r in records if r['deleted'] == '0']) == 0:
            self.canvas.set_empty_database()
        else:
            self.stack.append(_address_from_key(Key.from_str(records[0]['key'])))
            _display_by_address(self.stack[-1])

class FlashCardCanvas(QtWidgets.QWidget):
    def __init__(self, layout_engine):
        super(FlashCardCanvas, self).__init__()
        self.render = {
            'lines': [],
            'line_spacing': 30,
            'view_rect': None,
            'background': COLOURS['background']
        }

        self.engine = layout_engine

        self.EMPTY_LINE = {
            'font': QtGui.QFont(FONT_FAMILY, 12),
            'colour': COLOURS['foreground'],
            'text': ''
        }

    def set_empty_database(self):
        self.set_title('Nothing in the database yet.')
        self.set_text('Please enter some verses first.')

    def set_title(self, title):
        # accessor
        self.title = title

        title = {
            'font': QtGui.QFont(FONT_FAMILY, 20, QtGui.QFont.Black),
            'colour': COLOURS['title'],
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
        # remove everything except for the title
        lines = self.render['lines'][0:2]
        self.render['lines'] = lines

        while len(lines) < 2:
            lines.append(self.EMPTY_LINE)

        font = QtGui.QFont(FONT_FAMILY, 18)
        colour = COLOURS['foreground']

        layout = self.engine.layout(text)

        for text in layout:
            lines.append({
                'font': font,
                'colour': colour,
                'text': text
             })

    def keyPressEvent(self, event):
        if event.key() == Qt.Qt.Key_Up:
            window.stack[-1].move_up()
            _display_by_address(window.stack[-1])
        elif event.key() == Qt.Qt.Key_Down:
            window.stack[-1].move_down()
            _display_by_address(window.stack[-1])

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)

        self.render['view_rect'] = event.rect()
        qp.fillRect(event.rect(), COLOURS['background'])

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

def _peek():
    dest = window.jump_to_dialog.lineedit_jump_to.text()
    key = Key.from_str(dest)
    if key.chapter == None:
        key.chapter = '1'
    if key.verse == None:
        key.verse = '1'

    records = window.verse_table.select_all()
    matches = []
    for rec in records:
        reckey = Key.from_str(rec['key'])
        if reckey.book.lower().startswith(key.book.lower()) and \
           reckey.chapter == key.chapter and \
           reckey.verse == key.verse:
            matches.append(reckey)

    if len(matches) > 0:
        window.jump_to_dialog.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        window.stack.append(_address_from_key(matches[0]))

        _display_by_address(window.stack[-1])
        window.canvas.set_title('Peeking at: {0} (enter – jump, esc – cancel)'.format(window.canvas.title))
    else:
        window.jump_to_dialog.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        window.canvas.set_title('No Matches')
        window.canvas.set_text('Please enter a valid book abbreviation followed by chapter number.')

    window.canvas.update()

def _address_from_key(key):
    records = window.verse_table.select_all()
    sentences, lookup = sentences_cons2(records, key.book, key.chapter)
    sentence = sentences_index_by_verseno(sentences, lookup, key.verse)
    return Address(sentences, lookup, (key.book, key.chapter, sentence))

def _display_by_address(address):
    records = window.verse_table.select_all()
    sentences, lookup = sentences_cons2(records, address.book, address.chapter)
    sentence = sentences[address.sentence]
    label = sentence_make_label(sentence, address.book, address.chapter)

    window.canvas.set_title(label + ' (' + config.translation.upper() + ')')
    window.canvas.set_text(sentence['text'])
    window.canvas.update()

def _conclude_jump(result):
    if result == QtWidgets.QDialog.Accepted:
        address = window.stack[-1]
    else:
        address = window.stack[0]

    window.stack = [address]
    window.jump_to_dialog.lineedit_jump_to.clear()

    _display_by_address(address)

def _prepare_jump():
    if len(window.stack) > 0:
        window.jump_to_dialog.show()
    else:
        QtWidgets.QMessageBox.warning(window.gui, 'mvp – Jump to', 'Unable to jump right now.')

def sentences_cons2(records, book, chapter):
    sentences = []
    lookup = []
    keyprefix = ' '.join([book, chapter])

    matches = []
    for rec in records:
        key = Key.from_str(rec['key'])
        if key.book == book and \
           key.chapter == chapter and \
           rec['deleted'] == '0':
            matches.append({
                'key': key,
                'record': rec
            })

    verseseq = [match['record']['text']
                for match in sorted(matches,
                                    key=lambda m: int(m['key'].verse))]

    # step 1 split verses into a queue of partial or whole verses.
    indiciesseq = [sorted(_find_all_delimiters(text, SENTENCE_DELIMITERS)) for text in verseseq]
    splitsseq = []
    for i, text in enumerate(verseseq):
        splitsseq.append(_split_verse(i + 1, text, indiciesseq[i]))

    # flatten list of lists
    queue = [split for splits in splitsseq for split in splits]

    # step 2 process the queue to produce sentences and look up table.
    sentence = {
        'text': '',
        'textseq': [],
        'sources': []
    }
    for split in queue:
        sentence['textseq'].append(split['text'])
        sentence['sources'].append({
            'verse': split['origin'],
            'partid': split['partid'],
            'iswhole': split['iswhole']
        })

        if len(lookup) < split['origin']:
            lookup.append(len(sentences))

        if split['isfinal']:
            sentence['text'] = ' '.join(sentence['textseq'])
            sentences.append(sentence)
            sentence = {
                'text': '',
                'textseq': [],
                'sources': []
            }

    return (sentences, lookup)

def sentences_find_by_verseno(sentences, lookup, verseno):
    i = int(verseno) - 1
    sentid = lookup[i]
    return sentences[sentid]

def sentences_index_by_verseno(sentences, lookup, verseno):
    i = int(verseno) - 1
    return lookup[i]

def sentence_make_label(sentence, book, chapter):
    srclist = []
    sources = sentence['sources']
    for source in sources:
        if source['iswhole']:
            srclist.append(str(source['verse']))
        else:
            srclist.append(str(source['verse']) + chr(ord('a') + source['partid']))
    return book + ' ' + chapter + ':' + ', '.join(srclist)

def _split_verse(verse, text, indices):
    split = []
    start = 0

    # use of lstrip() is due to a whitespace that follows a
    # punctuation.
    for j, index in enumerate(indices):
        split.append({
            'text': text[start:index + 1].lstrip(),
            'partid': j,
            'origin': verse,
            'isfinal': True,
            'iswhole': False
        })
        start = index + 1

    if len(text[start:]) > 0:
        split.append({
            'text': text[start:].lstrip(),
            'partid': len(split),
            'origin': verse,
            'isfinal': False,
            'iswhole': False
        })

    if len(split) == 1:
        split[0]['iswhole'] = True

    return split

def _find_all_delimiters(text, delimiters):
    indicies = []
    for delim in delimiters:
        index = text.find(delim, 0)
        while index >= 0:
            indicies.append(index)
            start = index
            index = text.find(delim, start + 1)
    return indicies

def debug_view_db():
    from dbgviewdb import DbgViewDb
    DbgViewDb().gui.show()

def debug_layout_engine():
    if len(window.stack) > 0:
        from dbglayout import DbgLayout
        from simplelayout import SimpleLayout
        from graphlayout import GraphLayout

        address = window.stack[0]

        records = window.verse_table.select_all()
        sentences, lookup = sentences_cons2(records, address.book, address.chapter)
        sentence = sentences[address.sentence]

        text = sentence['text']

        dbglayout = DbgLayout(window.gui)
        dbglayout.set_text(text)
        dbglayout.add_layout_engine(SimpleLayout())
        dbglayout.add_layout_engine(GraphLayout())
        dbglayout.show()
    else:
        QtWidgets.QMessageBox.warning(window.gui,
                                      'Debug – Layout Engines',
                                      'Unable to draw layouts')

def debug_sentences():
    if len(window.stack) > 0:
        from dbgsentences import DbgSentences
        address = window.stack[0]
        records = window.verse_table.select_all()
        (sentences, lookup) = sentences_cons2(records, address.book, address.chapter)
        info = DbgSentences()
        info.gui.label_source.setText('Sentences constructed from: '
                                      + ' '.join([address.book, address.chapter]))

        sentencesstr = ''
        for sentence in sentences:
            sentencesstr += ' - ' \
                + sentence_make_label(sentence, address.book, address.chapter) \
                + ': ' + sentence['text'] + '\n'
        info.gui.textedit_sentences.setPlainText(sentencesstr)

        lookupstr = ''
        for i, sentid in enumerate(lookup):
            lookupstr += 'Verse {0}: {1}\n'.format(1 + i, sentences[sentid]['text'])
        info.gui.textedit_lookup.setPlainText(lookupstr)

        info.gui.show()
    else:
        QtWidgets.QMessageBox.warning(window.gui, 'Debug – Sentences', 'Unable to show sentences')

def debug_display_graph():
    from dbggraph import DbgGraph

    if len(window.stack) > 0:
        address = window.stack[0]

        records = window.verse_table.select_all()
        sentences, lookup = sentences_cons2(records, address.book, address.chapter)
        sentence = sentences[address.sentence]

        text = sentence['text']

        dbggraph = DbgGraph()
        dbggraph.set_text(text)
        dbggraph.gui.show()
    else:
        QtWidgets.QMessageBox.warning(window.gui,
                                      'Debug – Display Graph',
                                      'Unable to display graph')
