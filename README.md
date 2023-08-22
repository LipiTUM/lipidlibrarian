# Lipid Librarian

## Build and Installation Instructions

To build the project you need to have sqlite3 installed and available in your Path.
Optionally, to rebuild the LipidOntology data files, R needs to be installed and available in your Path.

### Virtual Environment

    make install

### Docker Container

    docker build -t lipid-librarian .

### Global Python Environment

TODO

### Rebuild LipidOntology Data Files

You can reuse the Makefile targets including the virtual environment created by `make install`:

    make install
    source venv/bin/activate
    pip install -r requirements.dev.txt
    python scripts/convert_lipidontology.py

## Run Lipid Librarian

### CLI

In case you installed Lipid Librarian into a virtual environment, make sure you activate it before with `source venv/bin/activate`.

    lipid-librarian "PC(18:1_20:0)" "410.243;0.01" "PC(56:8)"
    lipid-librarian .path/to/file
    cat .path/to/file | lipid-librarian

### Docker

    docker run lipid-librarian "PC(18:1_20:0)" "410.243;0.01" "PC(56:8)"

### Import Python Package

```python
from lipid_librarian.LipidQuery import *

query1 = LipidQuery("PC(18:1_20:0)").query()
query2 = LipidQuery("410.243;0.01").query()
query3 = LipidQuery("PC(56:8)").query()

for lipid in query1:
    print(repr(lipid))

for lipid in query2:
    print(format(lipid, 'json'))

for lipid in query3:
    print(format(lipid, 'html'))
```
