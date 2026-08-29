from typing import Any


def evaluate_agent_analysis(
    rule_based_analysis: dict[str, Any],
    log_analysis: dict[str, Any],
    similar_incidents: list[dict[str, Any]],
    relevant_runbooks: list[dict[str, Any]],
    diagnosis: dict[str, Any],
) -> dict[str, Any]:

    checks = []

    # -------------------------
    # CHECK 1: DIAGNOSIS EXISTS
    # -------------------------

    probable_root_cause = diagnosis.get(
        "probable_root_cause"
    )

    diagnosis_present = bool(
        probable_root_cause
    )

    checks.append(
        {
            "check": "diagnosis_present",
            "passed": diagnosis_present,
        }
    )

    # -------------------------
    # CHECK 2: CONFIDENCE RANGE
    # -------------------------

    confidence = diagnosis.get(
        "confidence",
        0.0,
    )

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    confidence_valid = (
        0.0 <= confidence <= 1.0
    )

    checks.append(
        {
            "check": "confidence_valid",
            "passed": confidence_valid,
            "value": confidence,
        }
    )

    # -------------------------
    # CHECK 3: EVIDENCE EXISTS
    # -------------------------

    evidence = diagnosis.get(
        "evidence",
        {}
    )

    evidence_present = bool(evidence)

    checks.append(
        {
            "check": "evidence_present",
            "passed": evidence_present,
        }
    )

    # -------------------------
    # CHECK 4: ACTIONS EXIST
    # -------------------------

    recommended_actions = diagnosis.get(
        "recommended_actions",
        [],
    )

    actions_present = (
        isinstance(
            recommended_actions,
            list,
        )
        and len(recommended_actions) > 0
    )

    checks.append(
        {
            "check": "recommended_actions_present",
            "passed": actions_present,
            "count": (
                len(recommended_actions)
                if isinstance(
                    recommended_actions,
                    list,
                )
                else 0
            ),
        }
    )

    # -------------------------
    # CHECK 5: LOG GROUNDING
    # -------------------------

    log_evidence = log_analysis.get(
        "evidence",
        [],
    )

    log_grounding_available = (
        len(log_evidence) > 0
    )

    checks.append(
        {
            "check": "log_grounding_available",
            "passed": log_grounding_available,
            "evidence_count": len(
                log_evidence
            ),
        }
    )

    # -------------------------
    # CHECK 6: RUNBOOK GROUNDING
    # -------------------------

    runbook_grounding_available = (
        len(relevant_runbooks) > 0
    )

    checks.append(
        {
            "check": "runbook_grounding_available",
            "passed": runbook_grounding_available,
            "runbook_count": len(
                relevant_runbooks
            ),
        }
    )

    # -------------------------
    # CHECK 7: RETRIEVAL QUALITY
    # -------------------------

    strong_similar_incidents = [
        item
        for item in similar_incidents
        if item.get(
            "similarity",
            0,
        ) >= 0.70
    ]

    strong_runbooks = [
        item
        for item in relevant_runbooks
        if item.get(
            "similarity",
            0,
        ) >= 0.50
    ]

    retrieval_quality = (
        "strong"
        if (
            strong_similar_incidents
            or strong_runbooks
        )
        else "weak"
    )

    checks.append(
        {
            "check": "retrieval_quality",
            "passed": retrieval_quality
            == "strong",
            "value": retrieval_quality,
            "strong_similar_incidents": len(
                strong_similar_incidents
            ),
            "strong_runbooks": len(
                strong_runbooks
            ),
        }
    )

    # -------------------------
    # OVERALL SCORE
    # -------------------------

    passed_checks = sum(
        1
        for check in checks
        if check["passed"]
    )

    total_checks = len(checks)

    score = round(
        passed_checks / total_checks,
        2,
    )

    if score >= 0.85:
        status = "pass"
    elif score >= 0.60:
        status = "review"
    else:
        status = "fail"

    return {
        "status": status,
        "score": score,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "checks": checks,
        "guardrail_decision": (
            "allow_remediation_plan"
            if status == "pass"
            else "require_human_review"
        ),
    }