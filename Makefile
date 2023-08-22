# system python interpreter. used only to create virtual environment
PY = python3
VENV = venv
BIN=$(VENV)/bin

.PHONY: all
all: install test

external/lipidlynxx/README.md:
	git submodule update --init --recursive

/tmp/lipidlynxx: external/lipidlynxx/README.md
	cp -r external/lipidlynxx /tmp/

/tmp/lipidlynxx/pyproject.toml: /tmp/lipidlynxx
	./scripts/lipidlynxx_setuptools.sh /tmp/lipidlynxx

src/lipid_librarian/data:
	mkdir src/lipid_librarian/data
	mkdir src/lipid_librarian/data/alex123
	mkdir src/lipid_librarian/data/linex
	mkdir src/lipid_librarian/data/lipid_ontology
	cp data/adducts.csv src/lipid_librarian/data/
	cp data/alex123/alex123_db.h5 src/lipid_librarian/data/alex123/
	cp data/linex/linex_data.pbz2 src/lipid_librarian/data/linex/
	cp data/lipidontology/lion_graph.tsv src/lipid_librarian/data/lipid_ontology/
	cp data/lipidontology/lion_association.tsv src/lipid_librarian/data/lipid_ontology/

$(VENV):
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade wheel pip
	touch $(VENV)

.PHONY: build
build: $(VENV) pyproject.toml src/lipid_librarian/data /tmp/lipidlynxx/pyproject.toml
	$(BIN)/pip build .
	$(BIN)/pip bdist_wheel .

.PHONY: install
install: $(VENV) src/lipid_librarian/data /tmp/lipidlynxx/pyproject.toml
	$(BIN)/pip install .

.PHONY: lint
lint: $(VENV)
	$(BIN)/flake8 --ignore=E501 src

.PHONY: test
test: install
	$(BIN)/pytest test

.PHONY: clean
clean:
	rm -rf build
	rm -rf dist
	rm -rf lipid_librarian.egg-info
	rm -rf src/lipid_librarian.egg-info
	rm -rf src/lipid_librarian/data
	rm -rf /tmp/lipidlynxx
	rm -rf $(VENV)
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete
