from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

# Import all models so Alembic can detect them
import app.models.user        # noqa
import app.models.product     # noqa
import app.models.order       # noqa
import app.models.notification # noqa
import app.models.banner      # noqa
import app.models.sync_log    # noqa
import app.models.catalog     # noqa

from app.models.base import Base
from app.core.config import settings

config = context.config

# NOTE: Do NOT use config.set_main_option("sqlalchemy.url", ...) here.
# That call goes through Python's configparser which treats % as interpolation
# syntax — it breaks on URL-encoded ODBC connect strings (e.g. %3D, %7B).
# Instead we pass the URL directly to create_engine() in both modes below.

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL script)."""
    context.configure(
        url=settings.db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    engine_kwargs: dict = {"poolclass": pool.NullPool}
    # Legacy "SQL Server" driver + SQLAlchemy 2 → HY104 without this
    if settings.odbc_driver == "SQL Server":
        engine_kwargs["use_setinputsizes"] = False
    connectable = create_engine(
        settings.db_url,
        connect_args={"timeout": 30},
        **engine_kwargs,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQL Server cannot ALTER COLUMN inside one long uncommitted DDL
            # transaction (revision 002 hangs). Commit after each revision.
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
