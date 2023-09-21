# system python interpreter. used only to create virtual environment
PY = python3
VENV = venv
BIN=$(VENV)/bin

.PHONY: all
all: install test

$(VENV):
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade wheel gdown pytest flake8 pip
	touch $(VENV)

external/lipidlynxx/README.md:
	git submodule update --init --recursive

/tmp/lipidlynxx: external/lipidlynxx/README.md
	cp -r external/lipidlynxx /tmp/

/tmp/lipidlynxx/pyproject.toml: /tmp/lipidlynxx
	./scripts/lipidlynxx_setuptools.sh /tmp/lipidlynxx

data/alex123/alex123_db.h5: $(VENV)
	mkdir -p data/alex123
	$(BIN)/gdown 1PCyaofEvpOkysWM_zMUPjU-xIJSPzQVH -O data/alex123/alex123_db.h5

data/lion/lion_ontology_graph.obo: $(VENV)
	mkdir -p data/lion
	$(BIN)/gdown 1W5x38nUKKAv12N7f8RTqZ09hpSaLz8Cv -O data/lion/lion_ontology_graph.obo

data/lion/lion_association_table.tsv: $(VENV)
	mkdir -p data/lion
	$(BIN)/gdown 1bhdBM3LgBH9W74zn9seJeup-H9FFG7RN -O data/lion/lion_association_table.tsv

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
build: $(VENV) pyproject.toml src/lipidlibrarian/data /tmp/lipidlynxx/pyproject.toml
	$(BIN)/pip build .
	$(BIN)/pip sdist .
	$(BIN)/pip bdist_wheel .

.PHONY: install
install: $(VENV) src/lipidlibrarian/data /tmp/lipidlynxx/pyproject.toml
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
	rm -rf lipidlibrarian.egg-info
	rm -rf src/lipidlibrarian.egg-info
	rm -rf src/lipidlibrarian/data
	rm -rf /tmp/lipidlynxx
	rm -rf $(VENV)
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete
