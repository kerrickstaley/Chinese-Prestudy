import os.path
import sys
sys.path.append(os.path.dirname(__file__))

# import the main window object (mw) from aqt
from aqt import mw
# import all of the Qt GUI library
from aqt.qt import *
from PyQt5 import QtCore
import logging
# TODO need to package this with the extension
import jieba
# TODO need to package this with the extension
from cached_property import cached_property
# TODO need to package this with the extension
import chinese_vocab_list
# TODO need to package this with the extension
import chineseflashcards
# TODO need to package this with the extension
import genanki

RECOMMENDED_TARGET_VOCAB_SIZE = 3500

try:
    from typing import List, Optional, Set, Tuple
except ImportError:
    # Temporary hack until typing module is supported.
    from collections import defaultdict
    List = defaultdict(lambda: None)
    Optional = defaultdict(lambda: None)
    Set = defaultdict(lambda: None)
    Tuple = defaultdict(lambda: None)


def is_chinese_word(s):
    if not s:
        return False
    # TODO this is not a complete list, see
    # https://stackoverflow.com/questions/1366068/whats-the-complete-range-for-chinese-characters-in-unicode
    return all(0x4E00 <= ord(c) <= 0x9FFF for c in s)


class LineEditWithFocusedSignal(QLineEdit):
    focused = pyqtSignal()

    def focusInEvent(self, e):
        self.focused.emit()


class ChinesePrestudy:
    """
    Class that manages all the state associated with the Chinese Prestudy add-on.
    """

    @classmethod
    def instantiate_and_run(cls):
        cls().show_text_entry_window()

    def show_text_entry_window(self):
        """
        Show the first window of the utility. This window prompts the user to paste in some text.
        """
        self.text_entry_window = w = QWidget(mw, flags=QtCore.Qt.Window)
        w.setWindowTitle('Chinese Prestudy')

        vbox = QVBoxLayout()

        vbox.addWidget(QLabel('Paste in the Chinese text you want to read:'))

        self.input_text_box = QTextEdit()
        vbox.addWidget(self.input_text_box)

        continue_button = QPushButton('Continue')
        # TODO not sure why a lambda is needed here
        continue_button.clicked.connect(lambda: self.text_entry_continue_action())
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(continue_button)
        vbox.addLayout(hbox)

        w.setLayout(vbox)

        w.show()

    def text_entry_continue_action(self):
        self.input_text = self.input_text_box.toPlainText()
        self.text_entry_window.close()

        self.show_words_window()

    @cached_property
    def input_segmented(self) -> List[str]:
        """
        Return the input after segmenting into words.
        """
        jieba.setLogLevel(logging.ERROR)
        jieba.initialize()

        return list(jieba.cut(self.input_text))

    @cached_property
    def input_words(self) -> List[str]:
        """
        Return unique words in text, as a list, sorted by order of appearance in text.
        """
        rv = []
        seen_words = set()

        for word in self.input_segmented:
            if word in seen_words:
                continue
            if not is_chinese_word(word):
                continue

            seen_words.add(word)
            rv.append(word)

        return rv

    def show_words_window(self):
        """
        Show the second window of the utility. This window shows the new words that were extracted from the text.
        """
        self.words_window = QWidget(mw, flags=QtCore.Qt.Window)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('Enter your vocab size target:'))

        self.vocab_recommended_radio = QRadioButton('{} (Recommended)'.format(RECOMMENDED_TARGET_VOCAB_SIZE))
        self.vocab_custom_radio = QRadioButton('Custom: ')
        self.vocab_custom_box = LineEditWithFocusedSignal()

        radio_hbox = QHBoxLayout()
        radio_hbox.addStretch(1)
        radio_hbox.addWidget(self.vocab_recommended_radio)
        radio_hbox.addStretch(2)
        radio_hbox.addWidget(self.vocab_custom_radio)
        radio_hbox.addWidget(self.vocab_custom_box)
        radio_hbox.addStretch(1)
        vbox.addLayout(radio_hbox)

        vbox.addWidget(QLabel('These are the new words you should learn:'))

        self.words_and_defs_table = self.init_words_and_defs_table()
        vbox.addWidget(self.words_and_defs_table)

        continue_hbox = QHBoxLayout()
        continue_hbox.addStretch(1)
        continue_button = QPushButton('Continue')
        continue_hbox.addWidget(continue_button)
        vbox.addLayout(continue_hbox)

        self.words_window.setLayout(vbox)

        self.update_words_and_defs_table()

        # TODO: for some reason, this disables the blinking cursor in `vocab_custom_box`
        self.vocab_custom_box.focused.connect(lambda: self.vocab_custom_radio.click())
        self.vocab_recommended_radio.clicked.connect(lambda: self.update_words_and_defs_table())
        self.vocab_custom_radio.clicked.connect(lambda: self.update_words_and_defs_table())
        self.vocab_custom_box.textChanged.connect(lambda: self.update_words_and_defs_table())
        continue_button.clicked.connect(lambda: self.words_window_continue_action())

        self.words_window.show()

    def update_words_and_defs_table(self):
        words_to_study = self.words_to_study
        self.words_and_defs_table.setRowCount(len(words_to_study))
        for i, word in enumerate(self.words_to_study):
            self.words_and_defs_table.setItem(i, 0, QTableWidgetItem(word.simp))
            self.words_and_defs_table.setItem(i, 1, QTableWidgetItem(word.defs[0]))

    @property
    def words_to_study(self) -> List[chinese_vocab_list.VocabWord]:
        return self.get_words_to_study(self.word_target)

    @property
    def word_target(self):
        if self.vocab_recommended_radio.isChecked():
            return RECOMMENDED_TARGET_VOCAB_SIZE
        if self.vocab_custom_radio.isChecked():
            try:
                return int(self.vocab_custom_box.text())
            except ValueError:
                return 0
        return 0

    def get_words_to_study(self, target) -> List[chinese_vocab_list.VocabWord]:
        words = [w for w in self.all_words_to_study[:target] if w is not None]

        # re-sort to match input order
        # TODO this is inefficient
        def index(vocab_word):
            for i, input_word in enumerate(self.unknown_words):
                if input_word in [vocab_word.simp, vocab_word.trad]:
                    return i
            raise Exception

        return sorted(words, key=index)

    @cached_property
    def all_words_to_study(self) -> List[Optional[chinese_vocab_list.VocabWord]]:
        """
        Returns `vocab_list.words`, with `None` replacing elements that aren't in `input_text`.

        This allows us to quickly determine which words correspond to a given vocab target.
        """
        unknown_words_set = set(self.unknown_words)
        return [w if {w.simp, w.trad} & unknown_words_set else None for w in self.vocab_list.words]

    @cached_property
    def unknown_words(self) -> List[str]:
        """
        Get words in the text that aren't already studied.
        """
        return [word for word in self.input_words if word not in self.words_already_studied]

    @cached_property
    def words_already_studied(self) -> Set[str]:
        """
        Get words that are already studied, as a set.

        TODO this is a total hack right now.
        """
        # logic: a word is studied if there is a corresponding note with at least one card that is seen, or if there
        # is a corresponding note with all cards suspended
        def words_for_query(query):
            notes = [mw.col.getNote(id_) for id_ in mw.col.findNotes(query)]
            rv = set()
            for note in notes:
                rv.update(f for f in note.fields if is_chinese_word(f))
            return rv

        suspended = words_for_query('is:suspended')
        not_suspended = words_for_query('-is:suspended')
        not_new = words_for_query('-is:new')

        return not_new | (suspended - not_suspended)

    @property
    def input_with_hard_words_annotated(self) -> List[Tuple[str, Optional[chinese_vocab_list.VocabWord]]]:
        """
        Returns the input text, with "hard" words (words that are unknown and are above the study limit) annotated with
        definitions.

        The return format is a sequence of tuples (word, defn), where defn is None if the word is already known.
        Punctuation and newlines will also have their own tuples (with a None defn). It should be true that:

            ''.join(elem[0] for elem in self.input_with_hard_words_annotated) == self.input_text
        """
        # TODO we currently only cover words that appear in the Chinese Vocab List. Instead, we should synthesize
        #     VocabWords when they aren't in the vocab list.
        # TODO We're assuming simplified characters here.
        definitions = {word.simp: word for word in self.all_words_to_study if word is not None}
        to_define_set = set(definitions)
        to_define_set -= set(word.simp for word in self.words_to_study)

        rv = []
        for seg in self.input_segmented:
            if seg in to_define_set:
                rv.append((seg, definitions[seg]))
                to_define_set.remove(seg)
            else:
                rv.append((seg, None))

        return rv

    @cached_property
    def vocab_list(self):
        return chinese_vocab_list.VocabList.load()

    def init_words_and_defs_table(self, parent=None):
        """
        Generates a widget that displays a table of words and definitions.

        :param word_def_pairs: list of (word, def) tuples
        :return: a widget
        """
        return QTableWidget(0, 2, parent)

    def words_window_continue_action(self):
        final_touches_window = FinalTouchesWindow(self.words_to_study)

        self.words_window.close()
        final_touches_window.show()


class FinalTouchesWindow(QWidget):
    """
    Window 3/3, allows the user to set deck and tags.
    """

    def __init__(self, vocab_words: List[chinese_vocab_list.VocabWord]):
        super().__init__(mw, flags=QtCore.Qt.Window)
        self.vocab_words = vocab_words
        self.init_layout()

    def init_layout(self):
        self.setWindowTitle('Chinese Prestudy')

        vbox = QVBoxLayout()

        vbox.addWidget(QLabel('Select deck to add notes to:'))
        self.combo_box = QComboBox(self)
        self.combo_box.addItems(self.deck_names)
        vbox.addWidget(self.combo_box)

        vbox.addWidget(QLabel('(Optional) Enter tag(s) to add to notes, separated by spaces:'))
        self.tags_box = QLineEdit()
        vbox.addWidget(self.tags_box)

        hbox = QHBoxLayout()
        self.finish_button = QPushButton('Add Notes')
        hbox.addStretch(1)
        hbox.addWidget(self.finish_button)
        vbox.addLayout(hbox)

        self.finish_button.clicked.connect(lambda: self.add_notes_action())

        self.setLayout(vbox)

    @property
    def deck_names(self):
        return [d['name'] for d in self.decks]

    @property
    def decks(self):
        return sorted(list(mw.col.decks.decks.values()), key=lambda d: d['name'])

    def add_notes_action(self):
        # Checkpoint so user can undo later
        mw.checkpoint('Add Chinese Prestudy Notes')

        add_notes(self.vocab_words, self.combo_box.currentText(), self.tags_box.text().split())

        # Refresh main window view
        mw.reset()

        self.close()


def add_notes(vocab_words: List[chinese_vocab_list.VocabWord], deck_name: str, tags: List[str]):
    # get dict that describes deck
    deck = [d for d in mw.col.decks.decks.values() if d['name'] == deck_name][0]

    # By using the same ID and name as the existing deck, the notes are added to the existing deck, rather than going
    # into a new deck or the default deck.
    out_deck = chineseflashcards.ChineseDeck(deck['id'], deck_name)

    for vocab_word in vocab_words:
        note = out_deck.add_vocab_list_word(vocab_word, tags=tags)
        # Temporary hack: suspend everything except the "Simplified" card.
        # This should ideally be based on a GUI selector.
        for i, c in enumerate(note.cards):
            if i == 1:
                continue
            c.suspend = True

    # Write the data to the collection
    out_deck.write_to_collection_from_addon()


# create a new menu item, "Chinese Prestudy"
action = QAction('Chinese Prestudy', mw)
# set it to call ChinesePrestudy.instantiate_and_run when it's clicked
action.triggered.connect(ChinesePrestudy.instantiate_and_run)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
