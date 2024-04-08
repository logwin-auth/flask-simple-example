# Description

Simple example of flask + SQLalchemy database + strict pre-commit
validation + actions. Also, we configure alembic to support a
gorm-like update experience.

### Run Pre-commit Locally:

```bash
pre-commit run --all
```

### Run Flask (without saving database):

```bash
python3 -m flask run
```

### Run flask (saving to dev.db):

```bash
NOTE_DATABASE=sqlite+pysqlite:///dev.db python3 -m flask run
```