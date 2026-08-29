import json

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI()


def analyze_incident_with_llm(
    service_name: str,
    severity: str,
    error_message: str,
    description: str | None,
    rule_based_analysis: dict,
    similar_incidents: list[dict] | None = None,
    relevant_runbooks: list[dict] | None = None,
) -> dict:

    prompt = f"""
You are a senior Site Reliability Engineer and AI incident analyst.

Analyze the following production incident.

Service:
{service_name}

Severity:
{severity}

Error:
{error_message}

Description:
{description or "No description provided"}

Preliminary rule-based analysis:
{json.dumps(rule_based_analysis, indent=2)}

Relevant historical incidents retrieved from the vector database:
{json.dumps(similar_incidents or [], indent=2)}

Relevant troubleshooting runbooks retrieved from the vector database:
{json.dumps(relevant_runbooks or [], indent=2)}

Use historical incidents and runbooks only when they are relevant.

Do not assume that a historical incident has the same root cause merely because
it is similar.

Use runbooks as operational guidance, not as proof of the root cause.

Return a concise technical analysis containing:

1. probable_root_cause
2. explanation
3. confidence from 0.0 to 1.0
4. evidence
5. historical_context
6. relevant_runbook_guidance
7. recommended_actions

Do not invent evidence that is not present in:
- the current incident
- the rule-based analysis
- retrieved historical incidents
- retrieved runbooks

Clearly distinguish current-incident evidence from historical context and
runbook guidance.

Return valid JSON only.
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt,
    )

    return json.loads(response.output_text)