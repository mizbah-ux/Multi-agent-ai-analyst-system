from fastapi import FastAPI

from routes.health import router as health_router
from routes.upload import router as upload_router
from services.init_db import init_db
from routes.task import router as task_router
from routes.data_routes import router as data_agent_router
from routes.analysis_routes import router as analysis_agent_router
from routes.visualization_routes import router as visualization_router
from routes.report_routes import router as report_router
from routes.logs import router as logs_router
from fastapi.middleware.cors import CORSMiddleware
from routes.history import router as history_router
from routes.download import router as download_router
from routes.ppt import router as ppt_router
from auth.routes import router as auth_router
from routes.admin import router as admin_router
from routes.platform import router as platform_router
from routes.rag import router as rag_router
from routes.metrics import router as metrics_router
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from security.rate_limiter import RateLimitMiddleware

app = FastAPI(title="FlowIQ Orchestration Platform")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="FlowIQ Orchestration Platform",
        version="2.0.0",
        description="Secure AI workflow orchestration API with JWT, memory, tools, events, and evaluation.",
        routes=app.routes,
    )

    # 🔐 ADD SECURITY SCHEME
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # 🔐 APPLY GLOBALLY
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

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
app.include_router(admin_router)
app.include_router(platform_router)
app.include_router(rag_router)
app.include_router(metrics_router)
app.mount("/charts", StaticFiles(directory="charts"), name="charts")

@app.get("/")
def root():
    return {"message": "FlowIQ Orchestration Platform Running"}
