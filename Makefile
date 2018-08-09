test:
	cp __init__.py chinese_prestudy.py
	python -m pytest -vv tests/

package.zip:  __init__.py
	./package.py

.PHONY: install
install: package.zip
	rm -rf package
	mkdir package
	cp package.zip package
	cd package && unzip package.zip
	rm package/package.zip
	rm -rf "${HOME}"/.local/share/Anki2/addons21/chinese_prestudy
	cp -r package "${HOME}"/.local/share/Anki2/addons21/chinese_prestudy
