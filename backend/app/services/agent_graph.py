from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.incident_log import IncidentLog
from app.services.evaluation_service import evaluate_agent_analysis
from app.services.incident_analyzer import analyze_incident
from app.services.llm_analyzer import analyze_incident_with_llm
from app.services.log_analyzer import analyze_logs
from app.services.rag_service import (
    get_relevant_runbooks_for_rag,
    get_similar_incidents_for_rag,
)


class IncidentAgentState(TypedDict, total=False):
    incident: Incident
    db: Session

    supervisor_decision: str

    rule_based_analysis: dict[str, Any]
    log_analysis: dict[str, Any]

    similar_incidents: list[dict[str, Any]]
    relevant_runbooks: list[dict[str, Any]]

    diagnosis: dict[str, Any]
    evaluation: dict[str, Any]
    remediation_plan: dict[str, Any]


def supervisor_agent(
    state: IncidentAgentState,
) -> IncidentAgentState:
    incident = state["incident"]

    if incident.severity.lower() in {
        "critical",
        "high",
    }:
        decision = "full_investigation"
    else:
        decision = "standard_investigation"

    return {
        "supervisor_decision": decision,
    }


def signal_analysis_agent(
    state: IncidentAgentState,
) -> IncidentAgentState:
    incident = state["incident"]

    analysis = analyze_incident(
        service_name=incident.service_name,
        severity=incident.severity,
        error_message=incident.error_message,
        description=incident.description,
    )

    return {
        "rule_based_analysis": analysis,
    }


def log_analysis_agent(
    state: IncidentAgentState,
) -> IncidentAgentState:
    incident = state["incident"]
    db = state["db"]

    logs = (
        db.query(IncidentLog)
        .filter(
            IncidentLog.incident_id == incident.id
        )
        .order_by(
            IncidentLog.timestamp.asc()
        )
        .all()
    )

    analysis = analyze_logs(logs)

    return {
        "log_analysis": analysis,
    }


def retrieval_agent(
    state: IncidentAgentState,
) -> IncidentAgentState:
    incident = state["incident"]
    db = state["db"]

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

    return {
        "similar_incidents": similar_incidents,
        "relevant_runbooks": relevant_runbooks,
    }


def diagnosis_agent(
    state: IncidentAgentState,
) -> IncidentAgentState:
    incident = state["incident"]

    rule_based_analysis = state.get(
        "rule_based_analysis",
        {},
    )

    log_analysis = state.get(
        "log_analysis",
        {},
    )

    enriched_rule_analysis = {
        **rule_based_analysis,
        "log_analysis": log_analysis,
    }

    diagnosis = analyze_incident_with_llm(
        service_name=incident.service_name,
        severity=incident.severity,
        error_message=incident.error_message,
        description=incident.description,
        rule_based_analysis=enriched_rule_analysis,
        similar_incidents=state.get(
            "similar_incidents",
            [],
        ),
        relevant_runbooks=state.get(
            "relevant_runbooks",
            [],
        ),
    )

    return {
        "diagnosis": diagnosis,
    }


def evaluation_agent(
    state: IncidentAgentState,
) -> IncidentAgentState:

    evaluation = evaluate_agent_analysis(
        rule_based_analysis=state.get(
            "rule_based_analysis",
            {},
        ),
        log_analysis=state.get(
            "log_analysis",
            {},
        ),
        similar_incidents=state.get(
            "similar_incidents",
            [],
        ),
        relevant_runbooks=state.get(
            "relevant_runbooks",
            [],
        ),
        diagnosis=state.get(
            "diagnosis",
            {},
        ),
    )

    return {
        "evaluation": evaluation,
    }


def remediation_agent(
    state: IncidentAgentState,
) -> IncidentAgentState:
    diagnosis = state.get(
        "diagnosis",
        {},
    )

    evaluation = state.get(
        "evaluation",
        {},
    )

    recommended_actions = diagnosis.get(
        "recommended_actions",
        [],
    )

    immediate_actions = recommended_actions[:3]
    follow_up_actions = recommended_actions[3:]

    guardrail_decision = evaluation.get(
        "guardrail_decision"
    )

    remediation_allowed = (
        guardrail_decision
        == "allow_remediation_plan"
    )

    if remediation_allowed:
        remediation_status = "ready_for_human_approval"
        blocked_reason = None

    else:
        remediation_status = "withheld_pending_review"
        blocked_reason = (
            "Automated remediation actions were withheld "
            "because the investigation did not have enough "
            "supporting evidence to safely recommend execution."
        )

    remediation_plan = {
        "priority": (
            "urgent"
            if state.get(
                "supervisor_decision"
            ) == "full_investigation"
            else "normal"
        ),
        "status": remediation_status,
        "immediate_actions": (
            immediate_actions
            if remediation_allowed
            else []
        ),
        "follow_up_actions": (
            follow_up_actions
            if remediation_allowed
            else []
        ),
        "blocked_reason": blocked_reason,
        "guardrail_decision": guardrail_decision,
        "human_approval_required": True,
    }

    return {
        "remediation_plan": remediation_plan,
    }


def build_incident_agent_graph():
    graph = StateGraph(IncidentAgentState)

    graph.add_node(
        "supervisor_agent",
        supervisor_agent,
    )

    graph.add_node(
        "signal_analysis_agent",
        signal_analysis_agent,
    )

    graph.add_node(
        "log_analysis_agent",
        log_analysis_agent,
    )

    graph.add_node(
        "retrieval_agent",
        retrieval_agent,
    )

    graph.add_node(
        "diagnosis_agent",
        diagnosis_agent,
    )

    graph.add_node(
        "evaluation_agent",
        evaluation_agent,
    )

    graph.add_node(
        "remediation_agent",
        remediation_agent,
    )

    graph.set_entry_point(
        "supervisor_agent"
    )

    graph.add_edge(
        "supervisor_agent",
        "signal_analysis_agent",
    )

    graph.add_edge(
        "signal_analysis_agent",
        "log_analysis_agent",
    )

    graph.add_edge(
        "log_analysis_agent",
        "retrieval_agent",
    )

    graph.add_edge(
        "retrieval_agent",
        "diagnosis_agent",
    )

    graph.add_edge(
        "diagnosis_agent",
        "evaluation_agent",
    )

    graph.add_edge(
        "evaluation_agent",
        "remediation_agent",
    )

    graph.add_edge(
        "remediation_agent",
        END,
    )

    return graph.compile()


incident_agent_graph = build_incident_agent_graph()