from models.schemas import Base
from services.db_service import engine

def init_db():
    Base.metadata.create_all(bind=engine)