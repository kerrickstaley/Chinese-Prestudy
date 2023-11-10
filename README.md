# Chinese-Prestudy
Chinese-Prestudy is an Anki 2.1 plugin that helps you generate flashcards for a body of text so that you can learn the text's vocabulary before you read it.

There is more information, including usage instructions, in [this blog post](https://www.kerrickstaley.com/2018/09/04/chinese-prestudy).

[![Travis Build Status](https://travis-ci.com/kerrickstaley/Chinese-Prestudy.svg?branch=main)](https://travis-ci.com/kerrickstaley/Chinese-Prestudy)
[![Appveyor Build Status](https://ci.appveyor.com/api/projects/status/github/kerrickstaley/Chinese-Prestudy?branch=main&svg=true)](https://ci.appveyor.com/project/kerrickstaley/Chinese-Prestudy)

## Developing
If you want to contribute back to this project, follow these instructions:

### Setup
1. You'll want a computer running Linux. macOS may work too. Windows will not.
2. You need Anki 2.1 installed.
3. Install Python dependencies:
```
pip3 install --user chinesevocablist chineseflashcards genanki jieba cached_property chevron pyyaml
```

### Running
To try out your code, run
```
make install
```
and restart Anki to see the effects. You may need to uninstall your existing copy of the plugin if you got it from AnkiWeb, otherwise you'll have two copies of the plugin installed.

There are also some (currently, not very many) unit tests. You can run those with
```
make test
```

Some changes may belong in `chinesevocablist`, `chineseflashcards`, or `genanki`. If you want to change one of these packages, check it out from GitHub, make your change, and then run `make install` in the package's directory followed by `make install` in this directory and restart Anki.

## Publishing
If your name is Kerrick, you can publish new versions to AnkiWeb by following these steps:
1. Run `./package.py` to generate `package.ankiaddon`.
2. Install `package.ankiaddon` in Anki, and restart. Test thoroughly.
3. Go to https://ankiweb.net/shared/upload?id=882364911 and upload the new version of the package.
