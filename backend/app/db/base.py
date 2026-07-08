from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """All ORM models inherit from this. Imported by Alembic's env.py for autogenerate."""
    pass
