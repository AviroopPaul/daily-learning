import os
import json
import logging
from groq import Groq

logger = logging.getLogger(__name__)

GROQ_MODEL = os.getenv("GROQ_MODEL", "gpt-oss-120b")

TOPIC_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Concise, descriptive title e.g. 'Write-Ahead Logging for Crash Recovery'"
        },
        "domain": {
            "type": "string",
            "enum": [
                "Backend", "Frontend", "LLM Training", "LLM at Scale",
                "Deployment", "SCM", "Database", "Networking", "Security",
                "Observability", "Caching", "Distributed Systems", "Message Queues", "API Design"
            ]
        },
        "difficulty": {
            "type": "string",
            "enum": ["Beginner", "Intermediate", "Advanced"]
        },
        "problem_statement": {
            "type": "string",
            "description": "2-3 sentences clearly stating the core problem and why it's hard"
        },
        "context_text": {
            "type": "string",
            "description": "2-3 paragraphs on why this problem exists, when it occurs, and its business impact"
        },
        "deep_dive": {
            "type": "string",
            "description": "4-6 paragraphs of technical deep-dive covering key concepts, mechanisms, and trade-offs"
        },
        "real_world_examples": {
            "type": "string",
            "description": "3 concrete examples from companies like Netflix, Google, OpenAI, Meta, Uber. Each 2-3 sentences."
        },
        "solution_approaches": {
            "type": "string",
            "description": "2-3 approaches with trade-offs. Format: Approach name: description. Pros: ... Cons: ..."
        },
        "key_takeaways": {
            "type": "array",
            "items": {"type": "string"},
            "description": "5 concise bullet-point takeaways"
        },
        "further_reading": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3 related topics worth exploring next"
        }
    },
    "required": [
        "title", "domain", "difficulty", "problem_statement", "context_text",
        "deep_dive", "real_world_examples", "solution_approaches",
        "key_takeaways", "further_reading"
    ],
    "additionalProperties": False
}

SYSTEM_PROMPT = """You are an expert software architect and system design educator.
Your role is to create high-quality, educational content about real-world system design challenges.
You write in a clear, technical, yet accessible style — similar to top engineering blogs."""

TOPIC_PROMPT_TEMPLATE = """Generate a comprehensive system design educational topic for today ({date}).

Previously covered topics (DO NOT repeat these):
{previous_topics}

Focus on real challenges that companies like Netflix, Google, OpenAI, Anthropic, Meta, Uber, and Airbnb have faced and solved.
Choose a unique topic not in the list above. Be specific and insightful — avoid generic overviews."""


def generate_topic(date: str, previous_topics: list[str]) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")

    client = Groq(api_key=api_key)

    previous_str = "\n".join(f"- {t}" for t in previous_topics) if previous_topics else "None yet — this is the first topic!"

    prompt = TOPIC_PROMPT_TEMPLATE.format(
        date=date,
        previous_topics=previous_str,
    )

    logger.info(f"Generating topic for {date} using model {GROQ_MODEL}")

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=4096,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "daily_topic",
                "strict": True,
                "schema": TOPIC_SCHEMA,
            },
        },
    )

    content = response.choices[0].message.content
    logger.info("Structured output received, parsing")

    # With strict mode this will always be valid — parse and return
    data = json.loads(content)
    return data
