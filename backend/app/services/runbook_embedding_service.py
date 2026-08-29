from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI()


def create_runbook_embedding(
    title: str,
    category: str,
    content: str,
) -> list[float]:

    text = f"""
Title: {title}
Category: {category}
Content:
{content}
""".strip()

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )

    return response.data[0].embedding