from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()
database_url = settings.database_url
if database_url.startswith("sqlite:///./"):
    database_file = Path(__file__).resolve().parents[2] / database_url.removeprefix("sqlite:///./")
    database_url = f"sqlite:///{database_file}"
engine_options = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(database_url, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def check_database_connection() -> bool:
    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT 1")
    return True
