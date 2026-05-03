from fastapi import FastAPI

from routes.health import router as health_router
from routes.upload import router as upload_router
from services.init_db import init_db
from routes.task import router as task_router
from routes.data_agent import router as data_agent_router
from routes.analysis_agent import router as analysis_agent_router
from routes.visualization_agent import router as visualization_router
from routes.report_agent import router as report_router
from routes.logs import router as logs_router
from fastapi.middleware.cors import CORSMiddleware
from routes.history import router as history_router
from routes.download import router as download_router
from routes.ppt import router as ppt_router
from auth.routes import router as auth_router


app = FastAPI(title="AI Analyst System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the database
init_db()

# include routes
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(task_router)
app.include_router(data_agent_router)
app.include_router(analysis_agent_router)
app.include_router(visualization_router)
app.include_router(report_router)
app.include_router(logs_router)
app.include_router(history_router)
app.include_router(download_router)
app.include_router(ppt_router)
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "AI Analyst System Running"}