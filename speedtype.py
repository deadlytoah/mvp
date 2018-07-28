# coding: utf-8
"""Allows memorising verses by speed-typing.  At first all words are
shown as guidance.  But as the proficiency level increases, more and
more words are hidden.

"""

import config
import screen
from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from PyQt5 import uic
from address import Address
from key import Key
from random import randrange
from sdb import Sdb
from graphlayout import GraphLayout

Level1 = {
    'hidden_words': 0.0,
}

Level2 = {
    'hidden_words': 0.2,
}

Level3 = {
    'hidden_words': 0.5,
}

Level4 = {
    'hidden_words': 0.7,
}

Level5 = {
    'hidden_words': 1.0,
}

Levels = [Level1, Level2, Level3, Level4, Level5]

window = None

class SpeedTypeForm:
    """ main form for the speed type tutor style memorisation """

    def __init__(self):
        global window
        window = self

        self.jump_to_dialog = uic.loadUi('jump-to.ui')
        self.jump_to_dialog.lineedit_jump_to.textEdited.connect(_peek)
        self.jump_to_dialog.finished.connect(_conclude_jump)
        self.jump_to_dialog.move(0, 0)

        self.gui = uic.loadUi("speedtype.ui")
        self.gui.action_enter_verses.triggered.connect(_view_enter_verses)
        self.gui.action_view_flash_cards.triggered.connect(_view_flash_cards)
        self.gui.action_debug_inspect_database.triggered.connect(_debug_view_db)
        self.gui.action_debug_layout_engine.triggered.connect(_debug_layout_engine)
        self.gui.action_debug_sentences.triggered.connect(_debug_sentences)
        self.gui.action_display_graph.triggered.connect(_debug_display_graph)
        self.gui.action_jump_to.triggered.connect(_prepare_jump)

        self.gui.difficulty_level.valueChanged.connect(
            self._change_difficulty_level)

        self.canvas = SpeedTypeCanvas(GraphLayout())
        layout = QtWidgets.QVBoxLayout(self.gui.show_verses)
        layout.addWidget(self.canvas)
        self.canvas.setFocus(True)

        self.gui.title.setFont(QtGui.QFont(config.FONT_FAMILY, 20))

        self.database = Sdb(config.translation + config.DB_EXT).__enter__()
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

    def _change_difficulty_level(self):
        """user changed the difficulty level by manipulating the slider"""
        self.canvas.set_level(self.gui.difficulty_level.value())
        self.canvas.update()

class SpeedTypeCanvas(QtWidgets.QWidget):
    """Widget that fascilitates typing

    Displays text and lets user type it.  Hides a percentage of words
    according to the difficulty level.

    The text is left-aligned.  It is up to the parent widget to
    provide scrolling and layout.

    """
    def __init__(self, layout_engine):
        super(SpeedTypeCanvas, self).__init__()

        font = QtGui.QFont(config.FONT_FAMILY, 18)

        # describes how to render the canvas.
        self.render = {
            # 2D lists of letters, their colours and Cartesian
            # coordinates.  Each inner array corresponds to a line.
            'letters': [],

            # Set caret to the first letter of the first sentence.
            # This is line followed by column.
            'caret': (0, 0),
            'caret_colour': QtGui.QColor(config.COLOURS['caret']),

            'line_spacing': 30,
            'background': QtGui.QColor(config.COLOURS['background']),
            'font': font,
            'fm': QtGui.QFontMetrics(font),
        }

        # sequential storage of characters to display and their
        # states. This includes correct or incorrect entries and which
        # word each character belongs to.
        self.buf = []

        # the location of caret within self.buf.
        self.caret = 0

        # list of words and their states.
        self.words = []

        self.engine = layout_engine

    def set_empty_database(self):
        self.set_title('Nothing in the database yet.')
        self.set_text('Please enter some verses first.')

    def set_title(self, title):
        # accessor
        self.title = title
        window.gui.title.setText(self.title)

    def _init_char(self, ch):
        """Constructs a character.

        Constructs a character with its visibility state, whether user
        typed it correctly and the incorrect letter if typed
        incorrectly.

        """
        return {
            'char': ch,
            'word': None,
            'visible': True,
            'typed': None,
            'correct': False,
        }

    def _init_word(self):
        """Constructs a word.

        Constructs a word with its visibility state, reference to the
        last character of the word and whether it has been touched.

        """
        return {
            'word': '',
            'visible': True,
            'touched': False,
            'behind': False,
            'last_char': None,
        }

    def set_text(self, text):
        """Sets the text to be displayed in the canvas."""
        (self.buf, self.words) = self._process_text(text)
        self.caret = 0
        self.set_level(window.gui.difficulty_level.value())

        self._render()

    def _process_text(self, text):
        """Processes the given text.

        Produces character buffer and groups the words together.  The
        character buffer is used to show, hide and colour the letters.
        The list of words is used to show or hide words.

        """
        layout = self.engine.layout(text)
        buf = []
        words = []

        for text in layout:
            make_word = self._init_word()

            for ch in text:
                maybe_letter = self._init_char(ch)
                buf.append(maybe_letter)

                if config.WORD_DELIMITERS.find(ch) >= 0:
                    if len(make_word['word']) > 0:
                        words.append(make_word)
                        make_word = self._init_word()
                    else:
                        pass
                else:
                    maybe_letter['word'] = make_word
                    make_word['word'] = make_word['word'] + ch
                    make_word['last_char'] = len(buf) - 1

            # the last word in the line
            if len(make_word['word']) > 0:
                words.append(make_word)

            # end of line
            buf.append(self._init_char('\n'))

        return (buf, words)

    def set_level(self, level):
        """Sets the difficulty level.

        Sets the difficulty level and shows or hides some words as
        appropriate.

        """
        remaining = [w for w in self.words if w['behind'] == False]
        word_count = len(remaining)
        if word_count == 0:
            return
        hidden = len([w for w in remaining if w['visible'] == False])

        rate = hidden / word_count
        target = Levels[level]['hidden_words']

        if rate < target:
            # maybe hide more words
            count = 0
            while (hidden + count) / word_count <= target:
                count = count + 1
            # don't exceed the target
            count = count - 1

            if count > 0:
                self._hide_random_words(count)
        elif rate > target:
            # reveal some words
            count = 0
            while (hidden - count) / word_count > target:
                count = count + 1
            if count > 0:
                self._reveal_random_words(count)
            pass
        else:
            # do nothing
            pass

        self._render()

    def _hide_random_words(self, count):
        """hides a random list of count words"""
        # all shown words that are untouched
        words = [w for w in self.words
                 if w['visible'] == True and w['behind'] == False]
        for _ in range(0, count):
            pick = randrange(len(words))

            # Not hiding words that have been touched.  This means the
            # hidden word ratio may sometimes be a little wrong, but
            # we don't care about accuracy here.
            if words[pick]['touched'] == False:
                self._hide_word(words[pick])

            del words[pick]

    def _reveal_random_words(self, count):
        """reveals a random list of count words"""
        # all hidden words that are untouched
        words = [w for w in self.words
                 if w['visible'] == False and w['behind'] == False]
        for _ in range(0, count):
            pick = randrange(len(words))
            self._show_word(words[pick])
            del words[pick]

    def _hide_word(self, word):
        """hides a specific word"""
        word['visible'] = False
        for ch in [ch for ch in self.buf if ch['word'] is word]:
            ch['visible'] = False

    def _show_word(self, word):
        """shows a specific word"""
        word['visible'] = True
        for ch in [ch for ch in self.buf if ch['word'] is word]:
            ch['visible'] = True

    def keyPressEvent(self, event):
        if event.key() == Qt.Qt.Key_Up:
            window.stack[-1].move_up()
            _display_by_address(window.stack[-1])
        elif event.key() == Qt.Qt.Key_Down:
            window.stack[-1].move_down()
            _display_by_address(window.stack[-1])
        elif event.key() == Qt.Qt.Key_Backspace:
            pass
        elif event.text() != '':
            ch = self._char_at_caret()
            ch['typed'] = event.text()
            if event.text() == ch['char']:
                ch['correct'] = True
            else:
                ch['correct'] = False

            maybe_word = self._word_at_caret()
            if maybe_word is not None:
                word = maybe_word
                word['touched'] = True

                # we are at the last letter, which means we are done
                # with this word.
                if self.caret == word['last_char']:
                    word['behind'] = True

            _ = self._forward_caret()
            self._render()
            self.update()

    def _render(self):
        """Prepares the canvas for rendering.

        This method transforms the internal data into a data structure
        that can be used by paintEvent() method to draw the screen

        """
        letters = []
        y = 0
        x = 0
        for (i, ch) in enumerate(self.buf):
            if i == self.caret:
                self.render['caret'] = (x, y)

            if ch['char'] == '\n':
                x = 0
                y = y + self.render['line_spacing']
            else:
                if ch['typed'] is None:
                    if ch['visible'] == True:
                        (letter, colour) = (ch['char'], config.COLOURS['guide'])
                    else:
                        (letter, colour) = (' ', 'white')
                elif ch['correct'] == True:
                    (letter, colour) = self._render_correct_char(ch)
                else:
                    (letter, colour) = self._render_incorrect_char(ch)

                letters.append({
                    'letter': letter,
                    'colour': colour,
                    'coord': (x, y),
                })
                x = x + self.render['fm'].width(ch['char'])

        self.render['letters'] = letters

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.fillRect(event.rect(), self.render['background'])
        qp.setFont(self.render['font'])

        letters = self.render['letters']

        for letter in letters:
            self._render_letter(qp, self.render, letter)

        self._render_caret(qp, self.render, letters)
        qp.end()

    def _render_letter(self, qp, render, letter):
        ch = letter['letter']
        colour = QtGui.QColor(letter['colour'])
        coord = letter['coord']

        qp.setPen(colour)
        qp.drawText(coord[0], coord[1] + render['fm'].ascent(), ch)

    def _render_caret(self, qp, render, letters):
        (x, y) = render['caret']
        qp.setPen(render['caret_colour'])
        qp.drawLine(x, y, x, y + render['fm'].height())

    def _char_at_caret(self):
        """Returns the character at the caret"""
        return self.buf[self.caret]

    def _word_at_caret(self):
        """Returns the word at the caret

        Returns the word at the caret, or None if there is none found.

        """
        return self.buf[self.caret]['word']

    def _render_correct_char(self, char):
        """Handles the case where user typed the correct character"""
        return (char['char'], config.COLOURS['correct'])

    def _render_incorrect_char(self, char):
        """Handles the case where user typed the incorrect character"""
        word = char['word']
        if word is not None and word['visible'] == True:
            return (char['char'], config.COLOURS['incorrect'])
        else:
            return (char['typed'], config.COLOURS['incorrect'])

    def _forward_caret(self):
        """Moves caret forward by one letter

        If the caret is at the end of the text, returns False.
        Otherwise, advances the caret and returns True.

        """
        if self.caret + 1 >= len(self.buf):
            return False
        else:
            self.caret = self.caret + 1
            return True

def _view_flash_cards():
    """switch to the flash cards screen"""
    screen.switch_to(screen.FLASH_CARD_INDEX)

def _view_enter_verses():
    """switch to the verse entry screen"""
    screen.switch_to(screen.DATA_ENTRY_INDEX)

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
    indiciesseq = [sorted(_find_all_delimiters(text, config.SENTENCE_DELIMITERS))
                   for text in verseseq]
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

def _debug_view_db():
    from dbgviewdb import DbgViewDb
    DbgViewDb().gui.show()

def _debug_layout_engine():
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

def _debug_sentences():
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

def _debug_display_graph():
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
