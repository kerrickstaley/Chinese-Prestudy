# import the main window object (mw) from aqt
from aqt import mw
# import all of the Qt GUI library
from aqt.qt import *
from PyQt5 import QtCore


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
        w = QWidget(mw, flags=QtCore.Qt.Window)
        w.setWindowTitle('Chinese Prestudy')

        vbox = QVBoxLayout()

        vbox.addWidget(QLabel('Paste in the Chinese text you want to read:'))

        text_box = QTextEdit()
        vbox.addWidget(text_box)

        w.setLayout(vbox)

        w.show()


# create a new menu item, "test"
action = QAction("test", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(ChinesePrestudy.instantiate_and_run)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
