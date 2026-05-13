from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False

import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
Base = declarative_base()

engine = create_engine(
    DATABASE_URL,

    pool_pre_ping=True,

    pool_size=10,
    max_overflow=20,

    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
