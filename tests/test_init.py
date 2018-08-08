from mock import MagicMock
import types
import sys

def mock_imports():
  packages = [
    'aqt',
    'aqt.qt',
    'chineseflashcards',
    'genanki',
  ]
  objects = [
    'aqt.mw',
    'aqt.qt.QLineEdit',
    'aqt.qt.pyqtSignal',
    'aqt.qt.QWidget',
    'aqt.qt.QAction',
  ]

  for p in packages:
    sys.modules[p] = types.ModuleType(p)

  for o in objects:
    mod, name = o.rsplit('.', 1)
    setattr(sys.modules[mod], name, MagicMock())

mock_imports()

from chinese_prestudy import ChinesePrestudy


def test_input_words():
  cp = ChinesePrestudy()
  cp.input_text = '你好！我叫李可達。我喜歡攀岩。'

  assert cp.input_words == ['你好', '我', '叫', '李可達', '喜歡', '攀岩']
