import os.path
import sys
sys.path.append(os.path.dirname(__file__))

# import the main window object (mw) from aqt
from aqt import mw
# import all of the Qt GUI library
from aqt.qt import *
import logging
import jieba
from cached_property import cached_property
import chinesevocablist
import chineseflashcards
import genanki
import functools

RECOMMENDED_LEARN_WORDS_NUM = 3500
RECOMMENDED_SKIP_WORDS_NUM = 0

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


class TextEntryWindow(QWidget):
    def __init__(self):
        super().__init__(mw, flags=Qt.WindowType.Window)
        self.init_layout()

    def init_layout(self):
        self.setWindowTitle('Chinese Prestudy')

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

        self.setLayout(vbox)

    def text_entry_continue_action(self):
        input_text = self.input_text_box.toPlainText()
        self.close()
        words_window = WordsWindow(input_text)
        words_window.show()


class SelectedWords:
    def __init__(self):
        self._selected = {}
        self._set_by_user = {}

    @staticmethod
    def _key(word):
        return word.trad, word.simp

    def _handle_state_change(self, key, state):
        state = Qt.CheckState(state)
        self._set_by_user[key] = True
        if state == Qt.CheckState.Checked:
            self._selected[key] = True
        elif state == Qt.CheckState.Unchecked:
            self._selected[key] = False
        else:
            raise RuntimeError(f'unexpected state: {state}')

    def checkbox(self, word: chinesevocablist.VocabWord, default: bool) -> QCheckBox:
        key = self._key(word)

        if not self._set_by_user.setdefault(key, False):
            self._selected[key] = default

        ret = QCheckBox()
        ret.setChecked(self._selected[key])
        ret.stateChanged.connect(functools.partial(self._handle_state_change, key))
        return ret

    def selected(self, word: chinesevocablist.VocabWord) -> bool:
        return self._selected[self._key(word)]


class WordsWindow(QWidget):
    """
    Class that manages all the state associated with the Chinese Prestudy add-on.
    """
    def __init__(self, input_text):
        super().__init__(mw, flags=Qt.WindowType.Window)
        self.input_text = input_text
        self.selected_words = SelectedWords()
        self.init_layout()
        self.update_words_and_defs_table()

    def init_layout(self):
        """
        Show the second window of the utility. This window shows the new words that were extracted from the text.
        """
        config = mw.addonManager.getConfig(__name__)
        config.setdefault('study_words_num', RECOMMENDED_LEARN_WORDS_NUM)
        config.setdefault('skip_words_num', RECOMMENDED_SKIP_WORDS_NUM)

        vbox = QVBoxLayout()

        study_words_num_hbox = QHBoxLayout()
        self.study_words_num_box = QLineEdit()
        self.study_words_num_box.setText(str(config['study_words_num']))
        study_words_num_hbox.addWidget(QLabel('Study the most common'))
        study_words_num_hbox.addWidget(self.study_words_num_box)
        study_words_num_hbox.addWidget(QLabel('words (recommended: {})'.format(RECOMMENDED_LEARN_WORDS_NUM)))
        study_words_num_hbox.addStretch(1)
        vbox.addLayout(study_words_num_hbox)

        skip_words_num_hbox = QHBoxLayout()
        self.skip_words_num_box = QLineEdit()
        self.skip_words_num_box.setText(str(config['skip_words_num']))
        skip_words_num_hbox.addWidget(QLabel('...skipping the most common'))
        skip_words_num_hbox.addWidget(self.skip_words_num_box)
        skip_words_num_hbox.addWidget(QLabel('words (recommended: {})'.format(RECOMMENDED_SKIP_WORDS_NUM)))
        skip_words_num_hbox.addStretch(1)
        vbox.addLayout(skip_words_num_hbox)
        vbox.addWidget(QLabel('These are the new words you should learn:'))

        self.words_and_defs_table = self.init_words_and_defs_table()
        vbox.addWidget(self.words_and_defs_table)

        continue_hbox = QHBoxLayout()
        continue_hbox.addStretch(1)
        continue_button = QPushButton('Continue')
        continue_hbox.addWidget(continue_button)
        vbox.addLayout(continue_hbox)

        self.setLayout(vbox)

        self.study_words_num_box.textChanged.connect(lambda: self.update_words_and_defs_table())
        self.skip_words_num_box.textChanged.connect(lambda: self.update_words_and_defs_table())
        continue_button.clicked.connect(lambda: self.continue_action())

    def init_words_and_defs_table(self, parent=None):
        """
        Generates a widget that displays a table of words and definitions.

        :param word_def_pairs: list of (word, def) tuples
        :return: a widget
        """
        ret = QTableWidget(0, 3, parent)
        ret.setHorizontalHeaderLabels(['Hanzi', 'English', 'Add'])
        ret.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        ret.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        return ret

    def continue_action(self):
        config = mw.addonManager.getConfig(__name__)
        config['study_words_num'] = self.study_words_num
        config['skip_words_num'] = self.skip_words_num
        mw.addonManager.writeConfig(__name__, config)

        final_touches_window = FinalTouchesWindow([
            w for w in self.words_to_study if self.selected_words.selected(w)])

        self.close()
        final_touches_window.show()


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

    @cached_property
    def words_already_studied(self) -> Set[str]:
        """
        Get words that are already studied, as a set.

        TODO this is a total hack right now.
        """
        # logic: a word is studied if there is a corresponding note with at least one card that is seen, or if there
        # is a corresponding note with all cards suspended
        def words_for_query(query):
            notes = [mw.col.getNote(id_) for id_ in mw.col.find_notes(query)]
            rv = set()
            for note in notes:
                rv.update(f for f in note.fields if is_chinese_word(f))
            return rv

        suspended = words_for_query('is:suspended')
        not_suspended = words_for_query('-is:suspended')
        not_new = words_for_query('-is:new')

        return not_new | (suspended - not_suspended)

    @cached_property
    def unknown_words(self) -> List[str]:
        """
        Get words in the text that aren't already studied.
        """
        return [word for word in self.input_words if word not in self.words_already_studied]

    @cached_property
    def vocab_list(self):
        return chinesevocablist.VocabList.load()

    @cached_property
    def all_words_to_study(self) -> List[Optional[chinesevocablist.VocabWord]]:
        """
        Returns `vocab_list.words`, with `None` replacing elements that aren't in `input_text`.

        This allows us to quickly determine which words correspond to a given vocab target.
        """
        unknown_words_set = set(self.unknown_words)
        return [w if {w.simp, w.trad} & unknown_words_set else None for w in self.vocab_list.words]

    @property
    def study_words_num(self):
        try:
            return int(self.study_words_num_box.text())
        except ValueError:
            return 0

    @property
    def skip_words_num(self):
        try:
            return int(self.skip_words_num_box.text())
        except ValueError:
            return 0

    def get_words_to_study(self, study_words_num, skip_words_num) -> List[chinesevocablist.VocabWord]:
        words = [w for w in self.all_words_to_study[skip_words_num:study_words_num] if w is not None]

        # re-sort to match input order
        # TODO this is inefficient
        def index(vocab_word):
            for i, input_word in enumerate(self.unknown_words):
                if input_word in [vocab_word.simp, vocab_word.trad]:
                    return i
            raise Exception

        return sorted(words, key=index)

    @property
    def words_to_study(self) -> List[chinesevocablist.VocabWord]:
        return self.get_words_to_study(self.study_words_num, self.skip_words_num)

    def update_words_and_defs_table(self):
        words_to_study = self.words_to_study
        self.words_and_defs_table.setRowCount(len(words_to_study))

        def set_flags(item):
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable & ~Qt.ItemFlag.ItemIsSelectable)
            return item

        for i, word in enumerate(words_to_study):
            self.words_and_defs_table.setItem(i, 0, set_flags(QTableWidgetItem(word.simp)))
            self.words_and_defs_table.setItem(i, 1, set_flags(QTableWidgetItem(word.defs[0])))
            checkbox = self.selected_words.checkbox(word, True)
            self.words_and_defs_table.setCellWidget(i, 2, checkbox)

    @property
    def input_with_hard_words_annotated(self) -> List[Tuple[str, Optional[chinesevocablist.VocabWord]]]:
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

class FinalTouchesWindow(QWidget):
    """
    Window 3/3, allows the user to set deck and tags.
    """

    def __init__(self, vocab_words: List[chinesevocablist.VocabWord]):
        super().__init__(mw, flags=Qt.WindowType.Window)
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


def add_notes(vocab_words: List[chinesevocablist.VocabWord], deck_name: str, tags: List[str]):
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
# set it to show a TextEntryWindow
action.triggered.connect(lambda: TextEntryWindow().show())
# and add it to the tools menu
mw.form.menuTools.addAction(action)
