# import the main window object (mw) from aqt
from aqt import mw
# import all of the Qt GUI library
from aqt.qt import *
from PyQt5 import QtCore


# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.
def showTestWidget():
    w = QWidget(mw, flags=QtCore.Qt.Window)
    w.resize(250, 150)
    w.move(300, 300)
    w.setWindowTitle('Test Widget')
    w.show()


# create a new menu item, "test"
action = QAction("test", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(showTestWidget)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
