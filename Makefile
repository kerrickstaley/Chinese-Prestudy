.PHONY: install_deps
install_deps:
	# TODO: Use the Python zipfile module so we can remove this dependency.
	zip --version > /dev/null || { echo 'Error: Please install the "zip" utility using your system package manager (e.g. apt)'; exit 1; }
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

package.ankiaddon: __init__.py package.py
	./package.py

.PHONY: package
package: package.ankiaddon

uname := $(shell uname)
ifeq ($(uname), Linux)
    install_path := ${HOME}/.local/share/Anki2/addons21/chinese_prestudy
else ifeq ($(uname), Darwin)
    install_path := ${HOME}/Library/Application Support/Anki2/addons21/chinese_prestudy
else
    $(error Unknown OS ${uname})
endif

.PHONY: install
install: package.ankiaddon
	rm -rf package
	mkdir package
	cp package.ankiaddon package
	cd package && unzip package.ankiaddon
	rm package/package.ankiaddon
	rm -rf "${install_path}"
	cp -r package "${install_path}"
