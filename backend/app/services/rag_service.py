from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.runbook import Runbook


MIN_INCIDENT_SIMILARITY = 0.45
MIN_RUNBOOK_SIMILARITY = 0.45


def get_similar_incidents_for_rag(
    db: Session,
    incident: Incident,
    limit: int = 3,
) -> list[dict]:

    if incident.embedding is None:
        return []

    rows = (
        db.query(
            Incident,
            Incident.embedding.cosine_distance(
                incident.embedding
            ).label("distance"),
        )
        .filter(
            Incident.id != incident.id,
            Incident.embedding.is_not(None),
        )
        .order_by("distance")
        .limit(limit)
        .all()
    )

    results = []

    for similar_incident, distance in rows:
        similarity = 1 - float(distance)

        if similarity < MIN_INCIDENT_SIMILARITY:
            continue

        results.append(
            {
                "id": similar_incident.id,
                "service_name": similar_incident.service_name,
                "severity": similar_incident.severity,
                "error_message": similar_incident.error_message,
                "description": similar_incident.description,
                "similarity": round(similarity, 4),
            }
        )

    return results


def get_relevant_runbooks_for_rag(
    db: Session,
    incident: Incident,
    limit: int = 3,
) -> list[dict]:

    if incident.embedding is None:
        return []

    rows = (
        db.query(
            Runbook,
            Runbook.embedding.cosine_distance(
                incident.embedding
            ).label("distance"),
        )
        .filter(
            Runbook.embedding.is_not(None),
        )
        .order_by("distance")
        .limit(limit)
        .all()
    )

    results = []

    for runbook, distance in rows:
        similarity = 1 - float(distance)

        if similarity < MIN_RUNBOOK_SIMILARITY:
            continue

        results.append(
            {
                "id": runbook.id,
                "title": runbook.title,
                "category": runbook.category,
                "content": runbook.content,
                "similarity": round(similarity, 4),
            }
        )

    return results