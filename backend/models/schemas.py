from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from services.db_service import Base
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime



class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    user_input = Column(Text)
    file_id = Column(String)
    status = Column(String, default="pending")
    result_path = Column(String, nullable=True)
    ppt_path = Column(String, nullable=True)
    created_at = Column(DateTime)
    
class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer)
    agent = Column(String)
    message = Column(String)
    status = Column(String)  # running / completed / failed
    timestamp = Column(DateTime, default=datetime.utcnow)


