from typing import Any

from app.models.incident_log import IncidentLog


def analyze_logs(
    logs: list[IncidentLog],
) -> dict[str, Any]:

    evidence = []
    patterns = []

    error_count = 0
    warning_count = 0

    oom_detected = False
    restart_detected = False
    heap_growth_detected = False
    memory_pressure_detected = False

    for log in logs:
        level = log.level.lower()
        message = log.message.lower()

        if level == "error":
            error_count += 1

        if level == "warning":
            warning_count += 1

        if "oomkilled" in message:
            oom_detected = True
            evidence.append(
                "Kubernetes OOMKilled event detected"
            )

        if "restart" in message:
            restart_detected = True
            evidence.append(
                "Repeated container or pod restarts detected"
            )

        if (
            "heap allocation increased" in message
            or "heap growth" in message
        ):
            heap_growth_detected = True
            evidence.append(
                "Continuous heap growth detected before restart"
            )

        if "memory pressure" in message:
            memory_pressure_detected = True
            evidence.append(
                "Kubernetes memory pressure detected"
            )

    if oom_detected:
        patterns.append(
            "Out-of-memory termination pattern"
        )

    if restart_detected:
        patterns.append(
            "Repeated restart pattern"
        )

    if heap_growth_detected:
        patterns.append(
            "Possible memory leak or unbounded allocation pattern"
        )

    if memory_pressure_detected:
        patterns.append(
            "Sustained memory pressure pattern"
        )

    confidence = 0.50

    if oom_detected:
        confidence += 0.20

    if heap_growth_detected:
        confidence += 0.15

    if restart_detected:
        confidence += 0.08

    if memory_pressure_detected:
        confidence += 0.05

    confidence = min(
        confidence,
        0.98,
    )

    probable_log_cause = "No strong log pattern detected"

    if (
        oom_detected
        and heap_growth_detected
    ):
        probable_log_cause = (
            "Memory exhaustion with possible "
            "memory leak or unbounded allocation"
        )

    elif oom_detected:
        probable_log_cause = (
            "Container memory exhaustion"
        )

    return {
        "log_count": len(logs),
        "error_count": error_count,
        "warning_count": warning_count,
        "probable_log_cause": probable_log_cause,
        "confidence": round(
            confidence,
            2,
        ),
        "patterns": patterns,
        "evidence": list(
            dict.fromkeys(evidence)
        ),
    }