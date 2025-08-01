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

    lipidlibrarian "PC(18:1_20:0)" "PE 38:1" "816.6477;0.001;+H+" "Cholesterol" "SLM:000487065"
    lipidlibrarian path/to/file
    cat path/to/file | lipidlibrarian

### Docker

    docker run lipidlibrarian "PC(18:1_20:0)" "PE 38:1" "816.6477;0.001;+H+" "Cholesterol" "SLM:000487065"

### Podman

    podman run lipidlibrarian "PC(18:1_20:0)" "PE 38:1" "816.6477;0.001;+H+" "Cholesterol" "SLM:000487065"

### Import Python Package

```python
from lipidlibrarian.LipidQuery import *

query1 = LipidQuery("PC(18:1_20:0)").query()
query2 = LipidQuery("PE 38:1").query()
query3 = LipidQuery("816.6477;0.001;+H+").query()
query4 = LipidQuery("Cholesterol").query()
query5 = LipidQuery("SLM:000487065").query()

for lipid in query1:
    print(repr(lipid))

for lipid in query2:
    print(format(lipid, 'json'))

for lipid in query3:
    print(format(lipid, 'html'))

for lipid in query4:
    print(repr(lipid))

for lipid in query5:
    print(repr(lipid))
```
