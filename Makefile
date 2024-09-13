# system python interpreter. used only to create virtual environment
PY = python3
VENV = venv
BIN=$(VENV)/bin

.PHONY: all
all: install test

$(VENV):
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade wheel gdown build pytest flake8 pip
	touch $(VENV)

external/lipidlynxx/README.md:
	git submodule update --init --recursive

build/lipidlynxx: external/lipidlynxx/README.md
	mkdir -p build
	cp -r external/lipidlynxx build/

build/lipidlynxx/pyproject.toml: build/lipidlynxx
	./scripts/lipidlynxx_setuptools.sh build/lipidlynxx

data/alex123/alex123_db.h5: $(VENV)
	mkdir -p data/alex123
	$(BIN)/gdown 1PCyaofEvpOkysWM_zMUPjU-xIJSPzQVH --continue -O data/alex123/alex123_db.h5

data/lion/lion_ontology_graph.obo: $(VENV)
	mkdir -p data/lion
	$(BIN)/gdown 1W5x38nUKKAv12N7f8RTqZ09hpSaLz8Cv --continue -O data/lion/lion_ontology_graph.obo

data/lion/lion_association_table.tsv: $(VENV)
	mkdir -p data/lion
	$(BIN)/gdown 1bhdBM3LgBH9W74zn9seJeup-H9FFG7RN --continue -O data/lion/lion_association_table.tsv

src/lipidlibrarian/data: data/alex123/alex123_db.h5 data/lion/lion_ontology_graph.obo data/lion/lion_association_table.tsv
	mkdir -p src/lipidlibrarian/data
	mkdir -p src/lipidlibrarian/data/alex123
	mkdir -p src/lipidlibrarian/data/linex
	mkdir -p src/lipidlibrarian/data/lion
	cp data/adducts.csv src/lipidlibrarian/data/
	cp data/alex123/alex123_db.h5 src/lipidlibrarian/data/alex123/
	cp data/linex/linex_data.pbz2 src/lipidlibrarian/data/linex/
	cp data/lion/lion_ontology_graph.obo src/lipidlibrarian/data/lion/
	cp data/lion/lion_association_table.tsv src/lipidlibrarian/data/lion/

.PHONY: build
build: $(VENV) pyproject.toml src/lipidlibrarian/data
	$(BIN)/python3 -m build

.PHONY: install
install: $(VENV) src/lipidlibrarian/data
	$(BIN)/pip install .

.PHONY: install_optional
install_optional: $(VENV) build/lipidlynxx/pyproject.toml
	$(BIN)/pip install build/lipidlynxx

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
	rm -rf lipidlibrarian.egg-info
	rm -rf src/lipidlibrarian.egg-info
	rm -rf src/lipidlibrarian/data
	rm -rf /tmp/lipidlynxx
	rm -rf $(VENV)
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete
