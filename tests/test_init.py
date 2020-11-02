from unittest import mock
import types
import sys

from chinesevocablist import VocabWord


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
    setattr(sys.modules[mod], name, mock.MagicMock())

mock_imports()

from chinese_prestudy import ChinesePrestudy

INPUT_TEXT = '你好！我叫李可達。我喜歡攀岩。'


def mock_words_already_studied(new=None):
  if new is None:
    new = {'你好', '我', '喜歡'}
  return mock.patch.object(ChinesePrestudy, 'words_already_studied', new=mock.PropertyMock(return_value=new))


def mock_vocab_list(new=None):
  if new is None:
    new = mock.MagicMock()
    new.words = [
        VocabWord(
          trad='我',
          simp='我',
          pinyin='wǒ',
          defs=[
            'I',
            'me',
          ]),
        VocabWord(
          trad='你好',
          simp='你好',
          pinyin='nǐ hǎo',
          defs=[
            'hello',
            'hi',
          ]),
        VocabWord(
          trad='叫',
          simp='叫',
          pinyin='jiào',
          defs=[
            'to be called',
            'to yell',
          ]),
        VocabWord(
          trad='喜歡',
          simp='喜欢',
          pinyin='xǐ huan',
          defs=[
            'to like',
          ]),
        VocabWord(
          trad='攀岩',
          simp='攀岩',
          pinyin='pān yán',
          defs=[
            'rock climbing',
          ]),
      ]

  return mock.patch.object(ChinesePrestudy, 'vocab_list', new=mock.PropertyMock(return_value=new))


def mock_study_words_num(new=3):
  return mock.patch.object(ChinesePrestudy, 'study_words_num', new=mock.PropertyMock(return_value=new))


def mock_skip_words_num(new=0):
  return mock.patch.object(ChinesePrestudy, 'skip_words_num', new=mock.PropertyMock(return_value=new))


def test_input_words():
  cp = ChinesePrestudy()
  cp.input_text = INPUT_TEXT

  assert cp.input_words == ['你好', '我', '叫', '李可達', '喜歡', '攀岩']


def test_unknown_words():
  cp = ChinesePrestudy()
  cp.input_text = INPUT_TEXT

  with mock_words_already_studied():
    assert cp.unknown_words == ['叫', '李可達', '攀岩']


def test_input_with_hard_words_annotated():
  cp = ChinesePrestudy()
  cp.input_text = INPUT_TEXT
  with mock_words_already_studied(), mock_vocab_list(), mock_study_words_num(), mock_skip_words_num():
    assert cp.input_with_hard_words_annotated == [
      ('你好', None),
      ('！', None),
      ('我', None),
      ('叫', None),
      ('李可達', None),
      ('。', None),
      ('我', None),
      ('喜歡', None),
      ('攀岩', VocabWord(trad='攀岩', simp='攀岩', pinyin='pān yán', defs=['rock climbing'])),
      ('。', None),

    ]
