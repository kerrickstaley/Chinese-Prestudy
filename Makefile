.PHONY: install_deps
install_deps:
	pip install -r requirements.txt --user

.PHONY: install_deps_venv
install_deps_venv:
	pip install -r requirements.txt

.PHONY: test
test: install_deps test_inner

.PHONY: test_venv
test_venv: install_deps_venv test_inner

.PHONY: test_inner
test_inner:
	cp __init__.py chinese_prestudy.py
	python -m pytest -vv tests/

package.zip:  __init__.py
	./package.py

.PHONY: package
package: package.zip

.PHONY: install
install: package.zip
	rm -rf package
	mkdir package
	cp package.zip package
	cd package && unzip package.zip
	rm package/package.zip
	rm -rf "${HOME}"/.local/share/Anki2/addons21/chinese_prestudy
	cp -r package "${HOME}"/.local/share/Anki2/addons21/chinese_prestudy
