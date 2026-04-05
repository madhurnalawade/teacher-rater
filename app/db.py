from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(settings.database_url, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def apply_mvp_schema_fixes() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if not table_names:
        return

    with engine.begin() as connection:
        if "users" in table_names:
            user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
            if "username" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(15)"))

            user_indexes = {index["name"] for index in inspect(engine).get_indexes("users")}
            if "ix_users_username" not in user_indexes:
                connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"))

        if "professors" in table_names:
            professor_columns = {column["name"] for column in inspect(engine).get_columns("professors")}
            if "photo_url" not in professor_columns:
                connection.execute(text("ALTER TABLE professors ADD COLUMN photo_url VARCHAR(1024)"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
