# Lipid Librarian

## Build and Installation Instructions

Make sure you've installed python 3.11 and are using this version to create the virtual environment as well. If you experience slow performance, consider running a local SQL server to serve the ALEX¹²³ database instead of reading it from a file, or disable ALEX¹²³ for your queries.

### Python Virtual Environment

    make install install_optional

### Docker Container

    docker build -t lipidlibrarian -f Containerfile .

### OCI Container for Docker/Podman/Kubernetes

    buildah build -t lipidlibrarian -f Containerfile .

## Test Lipid Librarian

Run pytest in the git root directory with a venv activated with LipidLibrarian installed. It is highly recommended to run a local ALEX123 SQL Database for performance reasons (see below)

    pytest

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

## Run a local ALEX¹²³ SQL Database

The performance of querying the ALEX¹²³ database is quite low, as the whole file has to be parsed into memory first. To alleviate this issue, run a local SQL database to serve the information from ALEX¹²³ to lipidlibrarian:

from an SQL dump file:

```
mkdir -p data/alex123/sql
gdown 1K5-PnK9HEA5L0Y79CaLgFMKOQGddDSgi -O data/alex123/sql/alex123_db.sql

podman  run --detach --name alex123-sql --env MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1 --env MARIADB_USER=alex123 --env MARIADB_PASSWORD=alex123 --env MARIADB_DATABASE=alex123 -p 3306:3306 -v ./data/alex123/sql:/docker-entrypoint-initdb.d:O  mariadb:latest
```

or alternatively:

```
podman run --detach --name alex123-sql --env MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1 --env MARIADB_USER=alex123 --env MARIADB_PASSWORD=alex123 --env MARIADB_DATABASE=alex123 -p 3306:3306  docker.io/library/mariadb:latest

sync_alex123_sql_database --sql mysql+pymysql://alex123:alex123@127.0.0.1:3306/alex123

lipidlibrarian --sql --sql-host 127.0.0.1 --sql-port 3306 --sql-user alex123 --sql-password alex123 --sql-database alex123 "PC(18:1_20:0)"
```

from this container you can create the SQL dump file:

```
podman exec alex123-sql mariadb-dump --user alex123 --password=alex123 alex123 > alex123_db.sql
```
