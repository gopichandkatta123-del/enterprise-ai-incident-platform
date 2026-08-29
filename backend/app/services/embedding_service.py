from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI()


def create_incident_embedding(
    service_name: str,
    error_message: str,
    description: str | None,
) -> list[float]:

    text = f"""
Service: {service_name}
Error: {error_message}
Description: {description or "No description provided"}
""".strip()

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )

    return response.data[0].embedding