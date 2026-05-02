from services.db_service import engine, Base
from models.schemas import Task

def init_db():
    Base.metadata.create_all(bind=engine)