from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# For now (simple):
DATABASE_URL = "sqlite:///./app.db"

# Later replace with RDS:
# DATABASE_URL = "postgresql://user:password@host:port/db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()