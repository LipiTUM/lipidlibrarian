# Lipid Librarian

## Build and Installation Instructions

### Python Virtual Environment

    make install install_optional

### Docker Container (Docker < 25.0.0)

    docker build -t lipidlibrarian -f Containerfile .

### Docker Container (Docker >= 25.0.0)

    docker buildx -t lipidlibrarian -f Containerfile .

### OCI Container for Docker/Podman/Kubernetes

    buildah build -t lipidlibrarian -f Containerfile .

## Run Lipid Librarian

### CLI

In case you installed Lipid Librarian into a 'venv' virtual environment, make sure you activate it before with `source venv/bin/activate`.

    lipidlibrarian "PC(18:1_20:0)" "410.243;0.01" "PC(56:8)"
    lipidlibrarian path/to/file
    cat path/to/file | lipidlibrarian

### Docker

    docker run lipidlibrarian "PC(18:1_20:0)" "410.243;0.01" "PC(56:8)"

### Podman

    podman run lipidlibrarian "PC(18:1_20:0)" "410.243;0.01" "PC(56:8)"

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
