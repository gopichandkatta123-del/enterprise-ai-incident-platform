from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.database import Base, engine

# Import SQLAlchemy models before create_all()
# so their tables are registered with Base.metadata.
from app.models.incident import Incident
from app.models.incident_log import IncidentLog
from app.models.runbook import Runbook
from app.models.agent_run import AgentRun
from app.models.remediation_approval import RemediationApproval


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Enterprise Agentic AI Incident Intelligence Platform",
    description=(
        "AI-powered incident investigation "
        "and root-cause analysis platform."
    ),
    version="0.3.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)