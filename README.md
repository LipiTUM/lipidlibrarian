# Lipid Librarian

## Build and Installation Instructions

To build the project you need to have sqlite3 installed and available in your Path.

### Virtual Environment

    make install

### Docker Container

    docker build -t lipidlibrarian .

### Global Python Environment

TODO

## Run Lipid Librarian

### CLI

In case you installed Lipid Librarian into a virtual environment, make sure you activate it before with `source venv/bin/activate`.

    lipidlibrarian "PC(18:1_20:0)" "410.243;0.01" "PC(56:8)"
    lipidlibrarian path/to/file
    cat path/to/file | lipidlibrarian

### Docker

    docker run lipidlibrarian "PC(18:1_20:0)" "410.243;0.01" "PC(56:8)"

### Import Python Package

```python
from lipidlibrarian.LipidQuery import *

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
