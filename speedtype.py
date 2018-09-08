# coding: utf-8
"""Allows memorising verses by speed-typing.  At first all words are
shown as guidance.  But as the proficiency level increases, more and
more words are hidden.

"""

import config
import model
import os
import screen
import session
from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from PyQt5 import uic
from address import Address
from caret import Caret
from key import Key
from random import randrange
from sentence import sentences_cons2, sentences_index_by_verseno
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

UiMainWindow, QMainWindow = uic.loadUiType('speedtype.ui')

class SpeedTypeForm(UiMainWindow, QMainWindow):
    """ main form for the speed type tutor style memorisation """

    resized = Qt.pyqtSignal()

    def __init__(self):
        super(SpeedTypeForm, self).__init__()
        self.setupUi(self)

        global window
        window = self
        self.gui = self

        self.action_enter_verses.triggered.connect(_view_enter_verses)
        self.action_view_flash_cards.triggered.connect(_view_flash_cards)
        self.action_edit_session.triggered.connect(self._edit_session)
        self.action_debug_inspect_database.triggered.connect(_debug_view_db)
        self.action_debug_sentences.triggered.connect(_debug_sentences)

        self.difficulty_level.valueChanged.connect(self._difficulty_level_changed)

        self.canvas = SpeedTypeCanvas(GraphLayout())
        layout = QtWidgets.QVBoxLayout(self.speedtype)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.canvas.setFocus(True)

        self.title.setFont(QtGui.QFont(config.FONT_FAMILY, 20))

    def _difficulty_level_changed(self, value):
        """called when user changes the difficulty level by manipulating the
        slider

        """
        self.canvas.set_level(value)

    def _edit_session(self):
        """Calls the speed type widget's edit_session method."""
        self.canvas.edit_session()

    def closeEvent(self, event):
        """Makes sure the session is stored before exiting."""
        self.canvas.persist_on_exit()
        event.accept()

    def resizeEvent(self, event):
        """Makes sure the dimensions are updated for algorithms."""
        self.resized.emit()

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
        fm = QtGui.QFontMetrics(font)

        # describes how to render the canvas.
        self.render = {
            # 2D lists of letters, their colours and Cartesian
            # coordinates.  Each inner array corresponds to a line.
            'letters': [],

            'caret': None,
            'line_spacing': 30,
            'background': QtGui.QColor(config.COLOURS['background']),
            'font': font,
            'fm': fm,

            # Build the table of y coord to a pair of letters.  The first
            # one is the letter that we should start painting if y is the
            # beginning of clip region.  The second one is the letter that
            # we should stop drawing if y is the end of clip region.
            'cliptable': None,
            'ct_info': None,
            'fontheight': fm.height(),
        }

        # sequential storage of characters to display and their
        # states. This includes correct or incorrect entries and which
        # word each character belongs to.
        self.buf = []

        # The caret.
        self.caret = None

        # list of words and their states.
        self.words = []

        # list of indices to words that belong to each sentence.
        self.sentences = []

        # a cache for font metrics for letters.
        self.fmcache = {}

        # timer to persist the session and user's progress.
        self.persist_timer = Qt.QTimer(self)
        self.persist_timer.setSingleShot(True)
        self.persist_timer.setInterval(config.PERSIST_INTERVAL)
        self.persist_timer.timeout.connect(self.persist_session)

        self.engine = layout_engine

    def set_missing_text(self):
        loc = self.session['range']['start']
        self.set_title(' '.join([loc['book'], str(loc['chapter'])]) +
                       ' (' + config.translation.upper() + ')')
        self.set_text('The text is missing for the selected verses.  ' +
                      'Please enter the text in the enter verses screen, ' +
                      'or edit the current session.')

    def set_title(self, title):
        # accessor
        self.title = title
        window.title.setText(self.title)

    def _init_char(self, ch):
        """Constructs a character.

        Constructs a character with its visibility state, whether user
        typed it correctly and the incorrect letter if typed
        incorrectly.

        """
        return {
            'char': ch,
            'whitespace': ch == ' ' or ch == '\n',
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
            'id': None,
            'word': '',
            'visible': True,
            'touched': False,
            'behind': False,
            'last_char': None,
        }

    def clear_text(self):
        """Clears the text"""
        self.buf = []
        self.words = []
        self.caret.charpos = 0

    def set_text(self, text):
        """Sets the text to be displayed in the canvas."""
        self.clear_text()

        (self.buf, self.words) = self._process_text(text)
        self.sentences = [[index for (index, _) in enumerate(self.words)]]

        self.caret.buflen = len(self.buf)
        self.caret.eobuf = len(self.buf) - 1
        self._render()

    def append_sentence(self, sentence_text):
        """Appends a sentence to the view.

        Caller of this method must clear any text that may already be
        on the view.  This can be done via clear_text().

        set_text() may take a long time to complete if text is very
        long.  This method lets you feed one sentence at a time.

        """
        (buf, words) = self._process_text(sentence_text)

        sentence = [len(self.words) + index for (index, _) in enumerate(words)]
        self.sentences.append(sentence)
        self.buf.extend(buf)
        self.words.extend(words)

        self.caret.buflen = len(self.buf)
        self.caret.eobuf = len(self.buf) - 1
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
                    word_index = len(words) + len(self.words)
                    maybe_letter['word'] = word_index
                    make_word['id'] = word_index
                    make_word['word'] = make_word['word'] + ch
                    make_word['last_char'] = len(buf) - 1

            # the last word in the line
            if len(make_word['word']) > 0:
                words.append(make_word)

            # end of line
            buf.append(self._init_char('\n'))

        return (buf, words)

    def set_level(self, level):
        """Sets the difficulty level."""
        self.session["level"] = level
        self.persist_session()
        self._apply_level(level)
        self._render()
        self.update()

    def _apply_level(self, level):
        """Applies the difficulty level.

        Sets the difficulty level and shows or hides some words as
        appropriate.

        """
        for sentence in self.sentences:
            words = [self.words[index] for index in sentence]
            self._apply_level_words(level, words)

    def _apply_level_words(self, level, words):
        """Applies the difficulty level in the given words.

        Sets the difficulty level and shows or hides some words as
        appropriate.

        """
        remaining = [w for w in words if w['behind'] == False]
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
                self._hide_random_words(words, count)
        elif rate > target:
            # reveal some words
            count = 0
            while (hidden - count) / word_count > target:
                count = count + 1
            if count > 0:
                self._reveal_random_words(words, count)
        else:
            # do nothing
            pass

    def _hide_random_words(self, words, count):
        """Hides the given number, count, of words from words."""
        assert(len(words) >= count)

        # all shown words that are untouched
        words = [w for w in words if w['visible'] == True and w['behind'] == False]
        for _ in range(0, count):
            pick = randrange(len(words))

            # Not hiding words that have been touched.  This means the
            # hidden word ratio may sometimes be a little wrong, but
            # we don't care about accuracy here.
            if words[pick]['touched'] == False:
                self._hide_word(words[pick])

            del words[pick]

    def _reveal_random_words(self, words, count):
        """Reveals the given number, count, of words from words."""
        assert(len(words) >= count)

        # all hidden words that are untouched
        words = [w for w in words if w['visible'] == False and w['behind'] == False]
        for _ in range(0, count):
            pick = randrange(len(words))
            self._show_word(words[pick])
            del words[pick]

    def _hide_word(self, word):
        """hides a specific word"""
        word['visible'] = False
        for ch in [ch for ch in self.buf if ch['word'] == word['id']]:
            ch['visible'] = False

    def _show_word(self, word):
        """shows a specific word"""
        word['visible'] = True
        for ch in [ch for ch in self.buf if ch['word'] == word['id']]:
            ch['visible'] = True

    def edit_session(self):
        """show dialog to edit the current session"""
        dialog = Qt.QDialog(self)
        uic.loadUi('edit-session.ui', dialog)

        dialog.edit_name.setText(self.session['name'])
        start = self.session['range']['start']
        dialog.edit_book_chapter.setText(start['book'] + ' ' + str(start['chapter']))
        dialog.edit_level.setText(str(self.session['level']))
        dialog.edit_strategy.setText(str(self.session['strategy']))

        if dialog.exec_() == Qt.QDialog.Accepted:
            name = None
            level = None
            book = None
            chapter = None
            if dialog.edit_name.text().strip() != '':
                name = dialog.edit_name.text().strip()
            else:
                # try again
                self.edit_session()
                return

            if dialog.edit_book_chapter.text().strip() != '':
                book, chapter = dialog.edit_book_chapter.text().split(None, 1)
            else:
                # try again
                self.edit_session()
                return

            if dialog.edit_level.text().strip() != '':
                level = int(dialog.edit_level.text())
            else:
                # try again
                self.edit_session()
                return

            sess = session.init()
            sess['name'] = name
            sess['level'] = level
            start = sess['range']['start']
            start['translation'] = config.translation
            start['book'] = book
            start['chapter'] = chapter
            self.session = sess

            session.store(self.session)
            self._start_session()

    def _start_session(self):
        """Prepares and begins the session"""
        global window

        loc = self.session['range']['start']
        book = loc['book']
        chapter = str(loc['chapter'])

        records = model.verse.find_by_book_and_chapter(book, int(chapter))
        sentences, _ = sentences_cons2(records)

        if len(sentences) > 0:
            label = self.session['name'] + ' ' + book + ' ' + chapter
            self.set_title(label + ' (' + config.translation.upper() + ')')

            self.clear_text()
            for sentence in sentences:
                text = sentence['text']

                # Remove square brackets [] found in some translation
                # because it's very awkward to type those in.
                text = text.replace('[', '').replace(']', '')

                self.append_sentence(text)

            # The index is expected to match the id property.
            assert([i for (i, w) in enumerate(self.words) if i == w['id']] ==
                   [word['id'] for word in self.words])

            # adjust difficulty level according to the session property.
            level = int(self.session['level'])
            window.difficulty_level.setValue(level)

            self._apply_level(level)
            self._render()
            if not self.caret.visible_in_viewport(window.speedtype.y()):
                # Defer this action until the initialisation
                # completes.
                Qt.QTimer.singleShot(0, self._reveal_caret)
            self.make_cliptable()
            self.update()
        else:
            info = Qt.QMessageBox()
            info.setWindowTitle("mvp")
            info.setText("Text missing for " + ' '.join([book, chapter]))
            info.setInformativeText("The text for the chosen bible verses " +
                                    "are missing from the database.  Would " +
                                    "you like to add it in the enter bible " +
                                    "verses screen?")
            info.setIcon(Qt.QMessageBox.Question)
            info.addButton(Qt.QMessageBox.Ok)
            info.addButton(Qt.QMessageBox.Cancel)
            answer = info.exec_()

            if answer == Qt.QMessageBox.Ok:
                # Redirect user to the data entry screen.
                _view_enter_verses()
            else:
                self.set_missing_text()
                self.make_cliptable()
                self.update()

    @Qt.pyqtSlot()
    def persist_session(self):
        """Persists the session and user's progress."""
        if self.buf is not None and self.words is not None:
            self.session['progress'] = {
                'buf': self.buf,
                'words': self.words,
                'sentences': self.sentences,
                'caret': self.caret.persist(),
                'title': self.title,
            }
        session.store(self.session)

    def _resume_session(self):
        """Read the persisted session from the disk and prepare it for
        resumption.

        """
        # Load or initialise the session
        try:
            sess = session.load()

            # Persisted translation is different from the current
            # translation.  Back up the old session file and start
            # anew.
            if sess is not None and \
               sess['range']['start']['translation'] != config.translation:
                print('translation mismatch - starting a new session')
                os.rename(session.SESSION_FILE, session.SESSION_FILE +
                          '.' + sess['range']['start']['translation'])
                sess = None
        except session.InvalidSessionError as e:
            print('failed to load session', e)
            # Make a backup of the broken session file.  The
            # documentation says this will fail on Windows if the
            # target file already exists.
            os.rename(session.SESSION_FILE, 'invalid-' + session.SESSION_FILE)
            sess = None

        # Resumption failed, initialise a new session.
        if sess is None:
            sess = session.init()

            # set the range to phl 1
            start = sess['range']['start']
            start['book'] = 'Phl'
            end = sess['range']['end']
            end['book'] = 'Phl'
            end['chapter'] = 1
            end['verse'] = 30
            end['sentence'] = 24
            sess['range'] = { 'start': start, 'end': end }

        self.session = sess

        if self.session['progress'] is not None:
            progress = self.session['progress']
            self.session['progress'] = None
        else:
            progress = None
 
        if progress is None:
            self._start_session()
        else:
            self.buf = progress['buf']
            self.words = progress['words']
            self.sentences = progress['sentences']
            self.caret.restore(progress['caret'])
            self.set_title(progress['title'])

            # adjust difficulty level according to the session property.
            level = int(self.session['level'])
            window.difficulty_level.setValue(level)

            self._apply_level(level)
            self._render()
            if not self.caret.visible_in_viewport(window.speedtype.y()):
                # Defer this action until the initialisation
                # completes.
                Qt.QTimer.singleShot(0, self._reveal_caret)
            self.make_cliptable()
            self.update()

    def showEvent(self, event):
        """Handles the first time show event to set up the session."""
        if not event.spontaneous():
            self.caret = Caret(self.render['fm'].height(),
                               window.scroll_area.viewport().height())
            window.resized.connect(self.update_caret_for_resize)

            self._resume_session()

    def keyPressEvent(self, event):
        if event.key() == Qt.Qt.Key_Backspace:
            if self.caret.backward():
                ch = self.buf[self.caret.charpos]
                ch['typed'] = None
                ch['correct'] = False
                if ch['word'] is not None:
                    word = self.words[ch['word']]
                    word['behind'] = False

                self.persist_timer.start()

                self._render()
                if not self.caret.visible_in_viewport(window.speedtype.y()):
                    self._reveal_caret()
                self.update()
            else:
                # caret at the beginning of the text
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
                if self.caret.charpos == word['last_char']:
                    word['behind'] = True

            self.persist_timer.start()

            if self.caret.forward():
                self._render()
                if not self.caret.visible_in_viewport(window.speedtype.y()):
                    self._reveal_caret()
                self.update()
            else:
                # Finished?
                self._render()
                self.update()
                Qt.QApplication.postEvent(self, SessionCompleteEvent())
        else:
            return super(SpeedTypeCanvas, self).keyPressEvent(event)

    def sessionCompleteEvent(self, event):
        """Handles the custom event SessionCompleteEvent.

        Doing this in an event lets the view to finish painting first.
        It launches a message box that congratulates user for
        finishing.

        """
        congrats = Qt.QMessageBox()
        congrats.setText("Congratulations!")
        level = int(self.session['level'])
        nextlevel = level + 1

        try_again = "Try Again"
        try_next = "Try Next Difficulty"
        choose_chapter = "Choose Another Chapter"

        if nextlevel >= len(Levels):
            congrats.setInformativeText("Would you like to try again?")
            congrats.addButton(try_again, Qt.QMessageBox.AcceptRole)
        else:
            congrats.setInformativeText("Would you like to try the next " +
                                        "difficulty?")
            congrats.addButton(try_next, Qt.QMessageBox.AcceptRole)
            level = nextlevel

        congrats.addButton(choose_chapter, Qt.QMessageBox.AcceptRole)
        _ = congrats.exec_()

        clicked = congrats.clickedButton()
        if clicked.text() == try_again or clicked.text() == try_next:
            self.session['level'] = level
            self._start_session()
        elif clicked.text() == choose_chapter:
            self.edit_session()
        else:
            assert False, "Unexpected button clicked"

    def persist_on_exit(self):
        """Persists the session and progress before exiting."""
        if self.persist_timer.isActive():
            self.persist_timer.stop()
            self.persist_session()

    def event(self, event):
        """Processes custom events."""
        if event.type() == SessionCompleteEvent.eventtype():
            self.sessionCompleteEvent(event)
            return True
        else:
            return super(SpeedTypeCanvas, self).event(event)

    def _render(self):
        """Prepares the canvas for rendering.

        This method transforms the internal data into a data structure
        that can be used by paintEvent() method to draw the screen

        """
        letters = []
        y = 0
        x = 0
        ct_info = []

        for (i, ch) in enumerate(self.buf):
            if i == self.caret.charpos:
                self.caret.pos = (x, y)

            if ch['char'] == '\n':
                x = 0
                y = y + self.render['line_spacing']
            else:
                if ch['typed'] is None:
                    if ch['visible'] == True:
                        (letter, colour) = (ch['char'], config.COLOURS['guide'])
                    elif ch['whitespace']:
                        (letter, colour) = (' ', 'white')
                    else:
                        (letter, colour) = ('_', config.COLOURS['underscore'])
                elif ch['correct'] == True:
                    (letter, colour) = self._render_correct_char(ch)
                else:
                    (letter, colour) = self._render_incorrect_char(ch)

                letters.append({
                    'letter': letter,
                    'colour': colour,
                    'coord': (x, y),
                })
                x = x + self._width(ch['char'])

                ct_info.append(y)

        self.render['letters'] = letters
        self.render['ct_info'] = ct_info
        self.render['caret'] = self.caret.render()

        # Fix the height of the canvas so the entire content may be
        # visible.
        if y > 0: self.setMinimumHeight(y + self.render['line_spacing'])

    def _width(self, char):
        """Provides caching for calculating the width of the character."""
        if not char in self.fmcache:
            self.fmcache[char] = self.render['fm'].width(char)
        return self.fmcache[char]

    def make_cliptable(self):
        """Populates the cliptable, used to paint only what is necessary."""
        cliptable = []
        ct_info = self.render['ct_info']
        fontheight = self.render['fontheight']

        if len(ct_info) > 0:
            for y in range(0, self.height()):
                (first, second) = (None, None)

                for (i, yclip) in enumerate(ct_info):
                    if y < yclip + fontheight:
                        first = i
                        break

                for i in range(len(ct_info) - 1, -1, -1):
                    yclip = ct_info[i]
                    if y > yclip:
                        second = i
                        break

                cliptable.append((first, second))
            self.render['cliptable'] = cliptable

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.fillRect(event.rect(), self.render['background'])
        qp.setFont(self.render['font'])

        letters = self.render['letters']
        cliptable = self.render['cliptable']

        if cliptable is not None:
            letter_start = cliptable[event.rect().y()][0]
            letter_end = cliptable[event.rect().y() + event.rect().height() - 1][1]

            for letter in letters[letter_start:letter_end + 1]:
                self._paint_letter(qp, self.render, letter)

        self._paint_caret(qp, self.render['caret'])
        qp.end()

    def _paint_letter(self, qp, render, letter):
        ch = letter['letter']
        colour = QtGui.QColor(letter['colour'])
        coord = letter['coord']

        qp.setPen(colour)
        qp.drawText(coord[0], coord[1] + render['fm'].ascent(), ch)

    def _paint_caret(self, qp, render):
        if render is not None:
            (x, y) = render['pos']
            qp.fillRect(x, y, render['width'], render['height'],
                        QtGui.QColor(render['colour']))

    @Qt.pyqtSlot()
    def _reveal_caret(self):
        """Scrolls the view so that the caret is visible."""
        ydelta = self.caret.ideal_ydelta()
        if ydelta > 0:
            ydelta = 0
        elif ydelta + self.caret.viewport_height > self.height():
            ydelta = 1 - self.height() + self.caret.viewport_height
        window.scroll_area.verticalScrollBar().setValue(-ydelta)

    @Qt.pyqtSlot()
    def update_caret_for_resize(self):
        """Updates the caret when the window resizes."""
        self.caret.viewport_height = window.scroll_area.viewport().height()

    def _char_at_caret(self):
        """Returns the character at the caret"""
        return self.buf[self.caret.charpos]

    def _word_at_caret(self):
        """Returns the word at the caret

        Returns the word at the caret, or None if there is none found.

        """
        if self.buf[self.caret.charpos]['word'] is not None:
            return self.words[self.buf[self.caret.charpos]['word']]
        else:
            return None

    def _render_correct_char(self, char):
        """Handles the case where user typed the correct character"""
        return (char['char'], config.COLOURS['correct'])

    def _render_incorrect_char(self, char):
        """Handles the case where user typed the incorrect character"""
        index = char['word']
        if index is not None and self.words[index]['visible'] == True:
            return (char['char'], config.COLOURS['incorrect'])
        else:
            return (char['typed'], config.COLOURS['incorrect'])

class SessionCompleteEvent(Qt.QEvent):
    """Custom event that is fired when the session is complete."""
    def __init__(self):
        """Initialises the SessionCompleteEvent."""
        super(SessionCompleteEvent, self).__init__(SessionCompleteEvent.eventtype())

    def eventtype():
        """Generates and returns the type ID of the event."""
        if not hasattr(SessionCompleteEvent, "_eventtype"):
            SessionCompleteEvent._eventtype = Qt.QEvent.registerEventType()
        return SessionCompleteEvent._eventtype

def _view_flash_cards():
    """switch to the flash cards screen"""
    screen.switch_to(screen.FLASH_CARD_INDEX)

def _view_enter_verses():
    """switch to the verse entry screen"""
    screen.switch_to(screen.DATA_ENTRY_INDEX)

def _address_from_key(key):
    records = model.verse.find_by_book_and_chapter(key.book, int(key.chapter))
    sentences, lookup = sentences_cons2(records)
    sentence = sentences_index_by_verseno(sentences, lookup, key.verse)
    return Address(sentences, lookup, (key.book, key.chapter, sentence))

def _debug_view_db():
    from dbgviewdb import DbgViewDb
    DbgViewDb().gui.show()

def _debug_sentences():
    from sentence import sentence_make_label
    from dbgsentences import DbgSentences

    global window
    loc = window.canvas.session['range']['start']
    address = _address_from_key(Key(loc['book'], loc['chapter'], str(1)))
    records = model.verse.find_by_book_and_chapter(address.book, int(address.chapter))
    (sentences, lookup) = sentences_cons2(records)
    info = DbgSentences()
    info.gui.label_source.setText('Sentences constructed from: '
                                  + ' '.join([address.book, str(address.chapter)]))

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
