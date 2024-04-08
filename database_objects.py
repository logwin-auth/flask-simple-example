"""Database objects for the demo flask app."""

import uuid
from typing import List

import alembic
import alembic.command
import alembic.config
import alembic.migration
import alembic.operations
from sqlalchemy import Engine, StaticPool, String, create_engine, text
from sqlalchemy.orm import Mapped, Session, mapped_column, registry, validates

sql_registry = registry()


@sql_registry.mapped_as_dataclass
class Note:
    """Database note object."""

    __tablename__ = "notes"

    note_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, nullable=False
    )
    note_title: Mapped[str] = mapped_column(String(), nullable=False)
    note_text: Mapped[str] = mapped_column(String(), nullable=False)

    def __init__(self, note_id: str, note_title: str, note_text: str) -> None:
        """Initialize the note object."""
        self.note_id = note_id
        self.note_title = note_title
        self.note_text = note_text

    @validates("note_id")
    def __validate_id(self, _: str, value: str) -> str:
        uuid.UUID(value)
        return value

    @validates("note_title")
    def __validate_title(self, _: str, value: str) -> str:
        if not value:
            raise ValueError("empty title")
        return value


def create_engine_migrate(host_db_url: str, echo: bool = False) -> Engine:
    """
    Produce an engine for the given host DB URL.

    This will either connect, or produce a set of SQL commands to migrate the
    database and raise an exception. Since we only make upgrades that are
    backwards compatible, this dramatically simplifies the database migration
    pathway.
    """
    engine = create_engine(
        host_db_url,
        echo=echo,
        # check_same_thread = False helps prevent thread conflicts in flask.
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Enable foreign keys if running in sqlite.
    if host_db_url.startswith("sqlite") or host_db_url.startswith("pysqlite"):
        with Session(engine) as db:
            db.execute(text("PRAGMA foreign_keys = ON;"))
            db.flush()
            db.commit()
    sql_registry.metadata.create_all(engine)
    with engine.connect() as conn:
        mc = alembic.migration.MigrationContext.configure(conn)
        diff = alembic.autogenerate.produce_migrations(
            mc, sql_registry.metadata
        )
    if not diff.upgrade_ops:
        raise ValueError("upgrade_ops was none")
    if not diff.upgrade_ops.ops:
        return engine
    mc = alembic.migration.MigrationContext(
        connection=None, dialect=engine.dialect, opts={"as_sql": True}
    )
    operations = alembic.operations.Operations(mc)
    stack: List[alembic.operations.MigrateOperation] = [diff.upgrade_ops]
    print("-" * 80)
    print("Copy and paste migrate:")
    print("-" * 80)
    while stack:
        elem = stack.pop(0)
        if hasattr(elem, "ops"):
            stack.extend(elem.ops)
        else:
            operations.invoke(elem)
    print("-" * 80)
    raise ValueError("sql must be manually migrated")
