from typing import Any


def analyze_incident(
    service_name: str,
    severity: str,
    error_message: str,
    description: str | None,
) -> dict[str, Any]:

    combined_text = f"{error_message} {description or ''}".lower()

    probable_root_cause = "Unknown"
    confidence = 0.45
    evidence = []
    recommended_actions = []

    if (
        "connection pool" in combined_text
        or "connection timeout" in combined_text
        or "database connection" in combined_text
    ):
        probable_root_cause = "Database connection pool exhaustion"
        confidence = 0.88

        evidence.append(
            "Database connection-related errors detected"
        )

        recommended_actions.extend(
            [
                "Check active database connections",
                "Inspect database connection pool utilization",
                "Review connection timeout configuration",
                "Check for recent traffic spikes",
            ]
        )

    if "500" in combined_text:
        evidence.append("HTTP 500 server errors detected")
        confidence = min(confidence + 0.03, 0.95)

    if "latency" in combined_text:
        evidence.append(
            "Application latency degradation detected"
        )
        confidence = min(confidence + 0.03, 0.95)

    if "memory" in combined_text:
        probable_root_cause = "Potential memory exhaustion"
        confidence = 0.82

        evidence.append(
            "Memory-related failure signal detected"
        )

        recommended_actions.extend(
            [
                "Check application memory utilization",
                "Inspect recent memory usage trends",
                "Look for memory leaks",
            ]
        )

    if "cpu" in combined_text:
        probable_root_cause = "Potential CPU saturation"
        confidence = 0.82

        evidence.append(
            "CPU-related performance signal detected"
        )

        recommended_actions.extend(
            [
                "Check CPU utilization",
                "Inspect high-consumption processes",
                "Review recent workload changes",
            ]
        )

    if not recommended_actions:
        recommended_actions = [
            "Inspect application logs",
            "Review recent deployments",
            "Check infrastructure metrics",
            "Compare with historical incidents",
        ]

    return {
        "service_name": service_name,
        "severity": severity,
        "probable_root_cause": probable_root_cause,
        "confidence": round(confidence, 2),
        "evidence": evidence,
        "recommended_actions": recommended_actions,
    }