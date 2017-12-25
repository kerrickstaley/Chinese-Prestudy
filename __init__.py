# import the main window object (mw) from aqt
from aqt import mw
# import all of the Qt GUI library
from aqt.qt import *
from PyQt5 import QtCore
# TODO need to package this with the extension
import jieba


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

        print(self.in_words)

    def get_words_from_text(self, text):
        return set(jieba.cut(text))


# create a new menu item, "test"
action = QAction("test", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(ChinesePrestudy.instantiate_and_run)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
