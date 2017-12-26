# import the main window object (mw) from aqt
from aqt import mw
# import all of the Qt GUI library
from aqt.qt import *
from PyQt5 import QtCore
# TODO need to package this with the extension
import jieba
# TODO need to package this with the extension
from cached_property import cached_property


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
    def input_words(self):
        """
        Return unique words in text, as a list, sorted by order of appearance in text.
        """
        rv = []
        seen_words = set()

        for word in jieba.cut(self.input_text):
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

        self.vocab_hsk_5_radio = QRadioButton('3000 (HSK 5+)')
        self.vocab_custom_radio = QRadioButton('Custom: ')
        self.vocab_custom_box = LineEditWithFocusedSignal()

        radio_hbox = QHBoxLayout()
        radio_hbox.addStretch(1)
        radio_hbox.addWidget(self.vocab_hsk_5_radio)
        radio_hbox.addStretch(2)
        radio_hbox.addWidget(self.vocab_custom_radio)
        radio_hbox.addWidget(self.vocab_custom_box)
        radio_hbox.addStretch(1)
        vbox.addLayout(radio_hbox)

        vbox.addWidget(self.words_and_defs_table_widget([('你好', 'hello'), ('的', '(possessive)')]))

        self.words_window.setLayout(vbox)

        # TODO: for some reason, this disables the blinking cursor in `vocab_custom_box`
        self.vocab_custom_box.focused.connect(lambda: self.vocab_custom_radio.click())

        self.words_window.show()

    @cached_property
    def unknown_words(self):
        """
        Get words in the text that aren't already in the collection.
        """
        return [word for word in self.input_words if word not in self.words_already_studied]

    @cached_property
    def words_already_studied(self):
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

    def words_and_defs_table_widget(self, word_def_pairs, parent=None):
        """
        Generates a widget that displays a table of words and definitions.

        :param word_def_pairs: list of (word, def) tuples
        :return: a widget
        """
        w = QTableWidget(len(word_def_pairs), 2, parent)
        for i, (word, def_) in enumerate(word_def_pairs):
            w.setItem(i, 0, QTableWidgetItem(word))
            w.setItem(i, 1, QTableWidgetItem(def_))

        return w


# create a new menu item, "test"
action = QAction("test", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(ChinesePrestudy.instantiate_and_run)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
