.PHONY: clean-pyc clean-build docs clean

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "dist - package"
	@echo "register - register package with PyPI"
	@echo "upload - package and upload current version to PyPI"
	@echo "release - make a new release, upload it to PyPI and push to Git"
	@echo "bumpminor - increment the minor version number of the next release"
	@echo "bumpmajor - increment the major version number of the next release"
	@echo "install - install the package to the active Python's site-packages"
	@echo "dev - install package and requirements in editable mode"
	@echo "env - make virtualenv"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

lint:
	flake8 celerycontrib.sqlalchemyscheduler tests

test:
	python setup.py test

test-all:
	tox

coverage:
	coverage run --source celerycontrib.sqlalchemyscheduler setup.py test
	coverage report -m
	coverage html
	open htmlcov/index.html

docs:
	rm -f docs/celerycontrib.sqlalchemyscheduler.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ celerycontrib.sqlalchemyscheduler
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

register:
	python setup.py bdist_wheel register -r devpi

upload:
	python setup.py bdist_wheel upload -r devpi

release: clean test-all
	bumpversion release
	python setup.py bdist_wheel upload -r devpi
	bumpversion --no-tag patch
	git push --tags

bumpminor:
	bumpversion --no-tag minor

bumpmajor:
	bumpversion --no-tag major

install: clean
	python setup.py install

dev: clean
	pip install -r requirements-dev.txt
	pip install -e .

env:
	bash -c "source `which virtualenvwrapper.sh` && mkvirtualenv -p python3.4 sqlalchemyscheduler"
