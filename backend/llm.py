import os
import json
import logging
from groq import Groq

logger = logging.getLogger(__name__)

GROQ_MODEL = os.getenv("GROQ_MODEL", "gpt-oss-120b")

# Runtime config — overrides defaults without redeployment
_runtime_config: dict = {
    "model": None,
    "system_prompt": None,
    "topic_prompt_template": None,
}


def get_llm_config() -> dict:
    return {
        "model": _runtime_config["model"] or GROQ_MODEL,
        "system_prompt": _runtime_config["system_prompt"] or SYSTEM_PROMPT,
        "topic_prompt_template": _runtime_config["topic_prompt_template"] or TOPIC_PROMPT_TEMPLATE,
    }


def update_llm_config(data: dict) -> None:
    for key in ("model", "system_prompt", "topic_prompt_template"):
        if key in data:
            _runtime_config[key] = data[key] or None  # empty string resets to default

TOPIC_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Concise, descriptive title e.g. 'Write-Ahead Logging for Crash Recovery'"
        },
        "domain": {
            "type": "string",
            "enum": [],  # populated dynamically from subject areas at generation time
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

Preferred subject areas (pick one that hasn't been covered recently):
{subject_areas}

Focus on real challenges that companies like Netflix, Google, OpenAI, Anthropic, Meta, Uber, and Airbnb have faced and solved.
Choose a unique topic not in the list above. Be specific and insightful — avoid generic overviews."""


def generate_topic(date: str, previous_topics: list[str], model: str = None, subject_areas: list[str] = None) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")

    client = Groq(api_key=api_key)
    cfg = get_llm_config()
    effective_model = model or cfg["model"]

    previous_str = "\n".join(f"- {t}" for t in previous_topics) if previous_topics else "None yet — this is the first topic!"
    subject_str = "\n".join(f"- {s}" for s in subject_areas) if subject_areas else "- All topics welcome"

    prompt = cfg["topic_prompt_template"].format(
        date=date,
        previous_topics=previous_str,
        subject_areas=subject_str,
    )

    # Build schema with domain enum from current subject areas
    schema = json.loads(json.dumps(TOPIC_SCHEMA))  # deep copy
    domains = subject_areas if subject_areas else ["General"]
    schema["properties"]["domain"]["enum"] = domains

    logger.info(f"Generating topic for {date} using model {effective_model}, domains={domains}")

    response = client.chat.completions.create(
        model=effective_model,
        messages=[
            {"role": "system", "content": cfg["system_prompt"]},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=4096,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "daily_topic",
                "strict": True,
                "schema": schema,
            },
        },
    )

    content = response.choices[0].message.content
    logger.info("Structured output received, parsing")

    # With strict mode this will always be valid — parse and return
    data = json.loads(content)
    return data
