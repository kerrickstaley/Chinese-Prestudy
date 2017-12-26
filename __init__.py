# import the main window object (mw) from aqt
from aqt import mw
# import all of the Qt GUI library
from aqt.qt import *
from PyQt5 import QtCore
# TODO need to package this with the extension
import jieba


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

        self.in_text_box = QTextEdit()
        vbox.addWidget(self.in_text_box)

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
        self.in_text = self.in_text_box.toPlainText()
        self.text_entry_window.close()

        self.in_words = self.get_words_from_text(self.in_text)

        self.show_words_window()

    def get_words_from_text(self, text):
        return set(jieba.cut(text))

    def show_words_window(self):
        self.words_window = w = QWidget(mw, flags=QtCore.Qt.Window)

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
