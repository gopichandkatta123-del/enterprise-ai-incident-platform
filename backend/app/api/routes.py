from datetime import datetime
from time import perf_counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.agent_graph import incident_agent_graph
from app.core.database import get_db

from app.models.agent_run import (
    AgentRun,
    AgentRunResponse,
)

from app.models.incident import (
    Incident,
    IncidentCreate,
    IncidentResponse,
)

from app.models.incident_log import (
    IncidentLog,
    IncidentLogCreate,
    IncidentLogResponse,
)

from app.models.runbook import (
    Runbook,
    RunbookCreate,
    RunbookResponse,
)

from app.models.remediation_approval import (
    RemediationApproval,
    RemediationApprovalResponse,
    RemediationDecisionCreate,
)

from app.services.embedding_service import create_incident_embedding
from app.services.incident_analyzer import analyze_incident
from app.services.llm_analyzer import analyze_incident_with_llm
from app.services.rag_service import (
    get_relevant_runbooks_for_rag,
    get_similar_incidents_for_rag,
)
from app.services.runbook_embedding_service import create_runbook_embedding


router = APIRouter()


@router.get("/")
def root():
    return {
        "project": "Enterprise Agentic AI Incident Intelligence Platform",
        "status": "running",
    }


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "incident-intelligence-api",
    }


# -------------------------
# INCIDENT ROUTES
# -------------------------

@router.post(
    "/incidents",
    response_model=IncidentResponse,
)
def create_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db),
):
    incident_record = Incident(
        service_name=incident.service_name,
        severity=incident.severity,
        error_message=incident.error_message,
        description=incident.description,
        timestamp=incident.timestamp,
    )

    db.add(incident_record)
    db.commit()
    db.refresh(incident_record)

    return incident_record


@router.get(
    "/incidents",
    response_model=list[IncidentResponse],
)
def get_incidents(
    db: Session = Depends(get_db),
):
    return db.query(Incident).all()


@router.post("/incidents/{incident_id}/analyze")
def analyze_incident_endpoint(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        return {
            "error": "Incident not found"
        }

    rule_based_analysis = analyze_incident(
        service_name=incident.service_name,
        severity=incident.severity,
        error_message=incident.error_message,
        description=incident.description,
    )

    similar_incidents = get_similar_incidents_for_rag(
        db=db,
        incident=incident,
        limit=3,
    )

    relevant_runbooks = get_relevant_runbooks_for_rag(
        db=db,
        incident=incident,
        limit=3,
    )

    llm_analysis = analyze_incident_with_llm(
        service_name=incident.service_name,
        severity=incident.severity,
        error_message=incident.error_message,
        description=incident.description,
        rule_based_analysis=rule_based_analysis,
        similar_incidents=similar_incidents,
        relevant_runbooks=relevant_runbooks,
    )

    return {
        "incident_id": incident.id,
        "rule_based_analysis": rule_based_analysis,
        "retrieved_similar_incidents": similar_incidents,
        "retrieved_runbooks": relevant_runbooks,
        "llm_analysis": llm_analysis,
    }


@router.post("/incidents/{incident_id}/embed")
def embed_incident(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        return {
            "error": "Incident not found"
        }

    embedding = create_incident_embedding(
        service_name=incident.service_name,
        error_message=incident.error_message,
        description=incident.description,
    )

    incident.embedding = embedding

    db.commit()
    db.refresh(incident)

    return {
        "incident_id": incident.id,
        "message": "Embedding generated and stored successfully",
        "embedding_dimensions": len(embedding),
    }


@router.get("/incidents/{incident_id}/similar")
def get_similar_incidents(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        return {
            "error": "Incident not found"
        }

    if incident.embedding is None:
        return {
            "error": "Incident does not have an embedding yet"
        }

    similar_incidents = get_similar_incidents_for_rag(
        db=db,
        incident=incident,
        limit=3,
    )

    return {
        "incident_id": incident_id,
        "similar_incidents": similar_incidents,
    }


@router.post("/incidents/{incident_id}/agent-analyze")
def agent_analyze_incident(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        return {
            "error": "Incident not found"
        }

    if incident.embedding is None:
        return {
            "error": "Incident does not have an embedding yet"
        }

    started_at = datetime.utcnow()
    timer_start = perf_counter()

    try:
        result = incident_agent_graph.invoke(
            {
                "incident": incident,
                "db": db,
            }
        )

        timer_end = perf_counter()
        completed_at = datetime.utcnow()

        latency_ms = round(
            (timer_end - timer_start) * 1000,
            2,
        )

        evaluation = result.get(
            "evaluation",
            {},
        )

        diagnosis = result.get(
            "diagnosis",
            {},
        )

        diagnosis_summary = diagnosis.get(
            "probable_root_cause"
        )

        agent_run = AgentRun(
            incident_id=incident.id,
            workflow="langgraph-agentic-analysis",
            started_at=started_at,
            completed_at=completed_at,
            latency_ms=latency_ms,
            evaluation_score=evaluation.get(
                "score"
            ),
            guardrail_decision=evaluation.get(
                "guardrail_decision"
            ),
            supervisor_decision=result.get(
                "supervisor_decision"
            ),
            diagnosis_summary=diagnosis_summary,
            status="success",
        )

        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)

        return {
            "incident_id": incident.id,
            "agent_run_id": agent_run.id,
            "workflow": "langgraph-agentic-analysis",
            "latency_ms": latency_ms,

            "supervisor_decision": result.get(
                "supervisor_decision"
            ),

            "rule_based_analysis": result.get(
                "rule_based_analysis",
                {},
            ),

            "log_analysis": result.get(
                "log_analysis",
                {},
            ),

            "retrieved_similar_incidents": result.get(
                "similar_incidents",
                [],
            ),

            "retrieved_runbooks": result.get(
                "relevant_runbooks",
                [],
            ),

            "agent_diagnosis": diagnosis,

            "evaluation": evaluation,

            "remediation_plan": result.get(
                "remediation_plan",
                {},
            ),
        }

    except Exception as exc:
        timer_end = perf_counter()
        completed_at = datetime.utcnow()

        latency_ms = round(
            (timer_end - timer_start) * 1000,
            2,
        )

        failed_run = AgentRun(
            incident_id=incident.id,
            workflow="langgraph-agentic-analysis",
            started_at=started_at,
            completed_at=completed_at,
            latency_ms=latency_ms,
            evaluation_score=None,
            guardrail_decision=None,
            supervisor_decision=None,
            diagnosis_summary=str(exc)[:500],
            status="failed",
        )

        db.add(failed_run)
        db.commit()

        raise


# -------------------------
# INCIDENT LOG ROUTES
# -------------------------

@router.post(
    "/incidents/{incident_id}/logs",
    response_model=IncidentLogResponse,
)
def create_incident_log(
    incident_id: int,
    log: IncidentLogCreate,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        return {
            "error": "Incident not found"
        }

    log_record = IncidentLog(
        incident_id=incident_id,
        level=log.level,
        source=log.source,
        message=log.message,
        timestamp=log.timestamp,
    )

    db.add(log_record)
    db.commit()
    db.refresh(log_record)

    return log_record


@router.get(
    "/incidents/{incident_id}/logs",
    response_model=list[IncidentLogResponse],
)
def get_incident_logs(
    incident_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(IncidentLog)
        .filter(
            IncidentLog.incident_id == incident_id
        )
        .order_by(
            IncidentLog.timestamp.asc()
        )
        .all()
    )


# -------------------------
# RUNBOOK ROUTES
# -------------------------

@router.post(
    "/runbooks",
    response_model=RunbookResponse,
)
def create_runbook(
    runbook: RunbookCreate,
    db: Session = Depends(get_db),
):
    runbook_record = Runbook(
        title=runbook.title,
        category=runbook.category,
        content=runbook.content,
    )

    db.add(runbook_record)
    db.commit()
    db.refresh(runbook_record)

    return runbook_record


@router.get(
    "/runbooks",
    response_model=list[RunbookResponse],
)
def get_runbooks(
    db: Session = Depends(get_db),
):
    return db.query(Runbook).all()


@router.post("/runbooks/{runbook_id}/embed")
def embed_runbook(
    runbook_id: int,
    db: Session = Depends(get_db),
):
    runbook = (
        db.query(Runbook)
        .filter(Runbook.id == runbook_id)
        .first()
    )

    if runbook is None:
        return {
            "error": "Runbook not found"
        }

    embedding = create_runbook_embedding(
        title=runbook.title,
        category=runbook.category,
        content=runbook.content,
    )

    runbook.embedding = embedding

    db.commit()
    db.refresh(runbook)

    return {
        "runbook_id": runbook.id,
        "message": "Runbook embedding generated and stored successfully",
        "embedding_dimensions": len(embedding),
    }


# -------------------------
# OBSERVABILITY / AUDIT ROUTES
# -------------------------

@router.get(
    "/agent-runs",
    response_model=list[AgentRunResponse],
)
def get_agent_runs(
    db: Session = Depends(get_db),
):
    return (
        db.query(AgentRun)
        .order_by(
            AgentRun.started_at.desc()
        )
        .all()
    )


@router.get(
    "/incidents/{incident_id}/agent-runs",
    response_model=list[AgentRunResponse],
)
def get_incident_agent_runs(
    incident_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(AgentRun)
        .filter(
            AgentRun.incident_id == incident_id
        )
        .order_by(
            AgentRun.started_at.desc()
        )
        .all()
    )


# -------------------------
# HUMAN APPROVAL ROUTES
# -------------------------

@router.post(
    "/agent-runs/{agent_run_id}/decision",
    response_model=RemediationApprovalResponse,
)
def create_remediation_decision(
    agent_run_id: int,
    decision: RemediationDecisionCreate,
    db: Session = Depends(get_db),
):
    agent_run = (
        db.query(AgentRun)
        .filter(
            AgentRun.id == agent_run_id
        )
        .first()
    )

    if agent_run is None:
        return {
            "error": "Agent run not found"
        }

    normalized_decision = (
        decision.decision
        .strip()
        .lower()
    )

    if normalized_decision not in {
        "approved",
        "rejected",
    }:
        return {
            "error": (
                "Decision must be either "
                "'approved' or 'rejected'"
            )
        }

    existing_decision = (
        db.query(RemediationApproval)
        .filter(
            RemediationApproval.agent_run_id
            == agent_run_id
        )
        .first()
    )

    if existing_decision is not None:
        existing_decision.decision = (
            normalized_decision
        )
        existing_decision.approved_by = (
            decision.approved_by
        )
        existing_decision.notes = decision.notes
        existing_decision.decided_at = (
            datetime.utcnow()
        )

        db.commit()
        db.refresh(existing_decision)

        return existing_decision

    approval = RemediationApproval(
        incident_id=agent_run.incident_id,
        agent_run_id=agent_run.id,
        decision=normalized_decision,
        approved_by=decision.approved_by,
        notes=decision.notes,
        decided_at=datetime.utcnow(),
    )

    db.add(approval)
    db.commit()
    db.refresh(approval)

    return approval


@router.get(
    "/agent-runs/{agent_run_id}/decision",
    response_model=RemediationApprovalResponse | None,
)
def get_remediation_decision(
    agent_run_id: int,
    db: Session = Depends(get_db),
):
    decision = (
        db.query(RemediationApproval)
        .filter(
            RemediationApproval.agent_run_id
            == agent_run_id
        )
        .first()
    )

    return decision


@router.get(
    "/remediation-decisions",
    response_model=list[RemediationApprovalResponse],
)
def get_all_remediation_decisions(
    db: Session = Depends(get_db),
):
    return (
        db.query(RemediationApproval)
        .order_by(
            RemediationApproval.decided_at.desc()
        )
        .all()
    )