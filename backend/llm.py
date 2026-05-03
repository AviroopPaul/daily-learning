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
    "difficulty_mode": None,  # None/"auto" | "Beginner" | "Intermediate" | "Advanced"
}

DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]

# Topic angles ensure variety across software engineering dimensions,
# not just the "scaling" frame the LLM defaults to.
TOPIC_ANGLES = [
    "Scaling & Distributed Systems",
    "Data Correctness & Consistency",
    "Security & Authentication",
    "Developer Experience & API Design",
    "Observability & Debugging",
    "Performance & Efficiency",
    "Reliability & Failure Recovery",
    "Software Development Practices",
]

# Keywords used to classify a topic title into one of the angles above.
_ANGLE_KEYWORDS: dict[str, list[str]] = {
    "Scaling & Distributed Systems": [
        "scal", "distributed", "multi-region", "global", "horizontal",
        "sharding", "partition", "replica", "cluster", "load balanc",
        "replication", "fan-out", "fanout",
    ],
    "Data Correctness & Consistency": [
        "consistency", "consensus", "exactly-once", "idempotent",
        "transaction", "acid", "lineariz", "serializab", "correctness",
        "isolation", "mvcc",
    ],
    "Security & Authentication": [
        "security", "auth", "oauth", "jwt", "encrypt", "tls", "ssl",
        "zero trust", "rbac", "access control", "secret", "csrf", "xss",
        "injection", "sandboxing",
    ],
    "Developer Experience & API Design": [
        "api design", "versioning", "sdk", "developer experience",
        "contract", "openapi", "graphql", "rest", "grpc", "webhook",
        "backward compat", "deprecat",
    ],
    "Observability & Debugging": [
        "observab", "monitor", "tracing", "logging", "metric",
        "alert", "debug", "profil", "telemetry", "slo", "sli", "sre",
        "flame graph", "distributed trace",
    ],
    "Performance & Efficiency": [
        "performance", "latency", "throughput", "cach", "compres",
        "optim", "efficiency", "cost", "ttl", "index", "query plan",
        "batch", "prefetch",
    ],
    "Reliability & Failure Recovery": [
        "reliab", "fault", "failover", "disaster", "recovery",
        "circuit break", "retry", "backoff", "chaos", "resilien",
        "graceful degradat", "bulkhead",
    ],
    "Software Development Practices": [
        "ci/cd", "deploy", "canary", "feature flag", "migration",
        "refactor", "test", "build", "release", "gitops", "blue-green",
        "rollback", "infrastructure as code",
    ],
}

# Angle descriptions injected into the prompt so the LLM understands the scope.
_ANGLE_DESCRIPTIONS: dict[str, str] = {
    "Scaling & Distributed Systems": (
        "how systems are designed or evolved to handle growth — sharding, replication, "
        "consistent hashing, multi-region architectures, etc."
    ),
    "Data Correctness & Consistency": (
        "correctness guarantees in distributed or concurrent systems — ACID transactions, "
        "consensus, idempotency, exactly-once delivery, MVCC, isolation levels, etc."
    ),
    "Security & Authentication": (
        "securing systems and data — OAuth flows, JWT pitfalls, encryption at rest/in transit, "
        "zero-trust networking, RBAC, secrets management, etc."
    ),
    "Developer Experience & API Design": (
        "how APIs and tooling are designed for the developers who consume them — versioning "
        "strategies, backward compatibility, OpenAPI, gRPC vs REST trade-offs, SDK design, etc."
    ),
    "Observability & Debugging": (
        "making systems understandable in production — distributed tracing, structured logging, "
        "SLOs/SLIs, alerting philosophy, profiling, flame graphs, etc."
    ),
    "Performance & Efficiency": (
        "squeezing more out of existing resources — query optimisation, caching strategies, "
        "compression, batching, prefetching, index design, cost reduction, etc."
    ),
    "Reliability & Failure Recovery": (
        "designing for inevitable failures — circuit breakers, retries with backoff, chaos "
        "engineering, graceful degradation, bulkheads, disaster recovery, etc."
    ),
    "Software Development Practices": (
        "engineering processes and deployment practices — CI/CD pipelines, canary/blue-green "
        "deployments, feature flags, database migrations, infrastructure-as-code, etc."
    ),
}


def infer_topic_angle(title: str) -> str:
    """Classify a topic title into one of TOPIC_ANGLES using keyword matching.

    Non-scaling angles are checked first so that a title like 'Exactly-Once Delivery in
    Distributed Queues' resolves to 'Data Correctness & Consistency' rather than being
    swallowed by the generic 'distributed' keyword. Scaling is the fallback."""
    title_lower = title.lower()
    priority_order = [a for a in TOPIC_ANGLES if a != "Scaling & Distributed Systems"] + ["Scaling & Distributed Systems"]
    for angle in priority_order:
        if any(kw in title_lower for kw in _ANGLE_KEYWORDS[angle]):
            return angle
    return "Scaling & Distributed Systems"


def compute_target_angle(recent_titles: list[str]) -> str:
    """Pick the angle least represented in recent topics, to counteract scaling bias."""
    counts = {a: 0 for a in TOPIC_ANGLES}
    for title in recent_titles:
        angle = infer_topic_angle(title)
        counts[angle] += 1
    # Exclude 'Scaling & Distributed Systems' from being chosen if it's already ≥ 2x
    # any other angle — hard-cap to prevent runaway dominance.
    min_non_scaling = min(
        counts[a] for a in TOPIC_ANGLES if a != "Scaling & Distributed Systems"
    )
    scaling_count = counts["Scaling & Distributed Systems"]
    candidates = TOPIC_ANGLES if scaling_count <= min_non_scaling else [
        a for a in TOPIC_ANGLES if a != "Scaling & Distributed Systems"
    ]
    return min(candidates, key=lambda a: counts[a])


def get_llm_config() -> dict:
    return {
        "model": _runtime_config["model"] or GROQ_MODEL,
        "system_prompt": _runtime_config["system_prompt"] or SYSTEM_PROMPT,
        "topic_prompt_template": _runtime_config["topic_prompt_template"] or TOPIC_PROMPT_TEMPLATE,
        "difficulty_mode": _runtime_config["difficulty_mode"] or "auto",
    }


def update_llm_config(data: dict) -> None:
    for key in ("model", "system_prompt", "topic_prompt_template", "difficulty_mode"):
        if key in data:
            _runtime_config[key] = data[key] or None  # empty string resets to default


def compute_target_difficulty(recent_difficulties: list[str]) -> str:
    """Pick the difficulty level least represented in recent topics."""
    counts = {d: 0 for d in DIFFICULTY_LEVELS}
    for d in recent_difficulties:
        if d in counts:
            counts[d] += 1
    # Pick the one with the lowest count; break ties in Beginner → Intermediate → Advanced order
    return min(DIFFICULTY_LEVELS, key=lambda d: counts[d])

TOPIC_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Concise, descriptive title e.g. 'Write-Ahead Logging for Crash Recovery'"
        },
        "tldr": {
            "type": "string",
            "description": "A 3-5 sentence plain-prose overview: (1) one sentence on the core problem, (2) the best solution approach and why it wins in 1-2 sentences, (3) 2-3 alternative approaches each in one sentence. No markdown, no bullet points."
        },
        "domain": {
            "type": "string",
            "enum": [],  # populated dynamically from subject areas at generation time
        },
        "difficulty": {
            "type": "string",
            "enum": DIFFICULTY_LEVELS
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
        "mermaid_diagram": {
            "type": "string",
            "description": (
                "A valid Mermaid.js diagram that visually illustrates the topic's architecture, "
                "data flow, or sequence of interactions. Pick the most appropriate diagram type: "
                "flowchart (LR or TD) for architectures, sequenceDiagram for request/response flows, "
                "stateDiagram-v2 for state machines, erDiagram for data models. "
                "Output ONLY raw Mermaid syntax — no markdown fences (```), no commentary. "
                "Start with the diagram type keyword on the first line. "
                "Keep it focused: 6-14 nodes, clear labels, no special characters that break Mermaid parsing "
                "(avoid parentheses, quotes, and colons inside node labels). "
                "Example: 'flowchart LR\\n  Client[Client] --> LB[Load Balancer]\\n  LB --> S1[Server 1]\\n  LB --> S2[Server 2]\\n  S1 --> DB[(Database)]\\n  S2 --> DB'"
            )
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
        "title", "tldr", "domain", "difficulty", "problem_statement", "context_text",
        "deep_dive", "real_world_examples", "solution_approaches", "mermaid_diagram",
        "key_takeaways", "further_reading"
    ],
    "additionalProperties": False
}

SYSTEM_PROMPT = """You are an expert software engineer and educator covering the full breadth of software development — \
system design, backend engineering, infrastructure, security, developer tooling, and engineering practices.
Your role is to create high-quality, practical educational content that working engineers find immediately useful.
You write in a clear, technical, yet accessible style — similar to top engineering blogs like the Netflix Tech Blog, \
AWS Architecture Blog, or Martin Fowler's bliki."""

TOPIC_PROMPT_TEMPLATE = """Generate a comprehensive software engineering educational topic for today ({date}).

Previously covered topics (DO NOT repeat these):
{previous_topics}

Preferred subject area (choose from these, picking one not recently covered):
{subject_areas}

Target difficulty: {target_difficulty}
The topic MUST be calibrated to the {target_difficulty} level — adjust depth, jargon, and assumed prior knowledge accordingly.

Today's angle: {target_angle}
Frame the topic through this lens: {angle_description}

IMPORTANT — diversity rules:
- Do NOT default to the "how do we scale this to millions of users" framing unless that is the stated angle.
- Scaling & distributed systems is just one of many valuable engineering topics. Security, correctness, \
developer experience, observability, and good engineering practices are equally important.
- Pick something a mid-to-senior engineer would find surprising, nuanced, or immediately applicable.
- Avoid generic interview-prep overviews. Be specific about the real trade-offs and failure modes.

Real-world grounding: Where relevant, reference how companies like Netflix, Google, Anthropic, Meta, \
Stripe, Cloudflare, or Shopify have approached this — but only when it illuminates the topic, not as a name-drop."""


def generate_tldr(title: str, problem_statement: str, solution_approaches: str, model: str = None) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")

    client = Groq(api_key=api_key)
    cfg = get_llm_config()
    effective_model = model or cfg["model"]

    prompt = (
        f"Topic: {title}\n\n"
        f"Problem: {problem_statement}\n\n"
        f"Solution approaches: {solution_approaches}\n\n"
        "Write a TL;DR for this system design topic in 3-5 sentences of plain prose (no markdown, no bullet points): "
        "(1) one sentence on the core problem, "
        "(2) the best solution approach and why it wins in 1-2 sentences, "
        "(3) 2-3 alternative approaches each in one sentence."
    )

    response = client.chat.completions.create(
        model=effective_model,
        messages=[
            {"role": "system", "content": cfg["system_prompt"]},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


def generate_topic(date: str, previous_topics: list[str], model: str = None, subject_areas: list[str] = None, target_difficulty: str = None, target_angle: str = None) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")

    client = Groq(api_key=api_key)
    cfg = get_llm_config()
    effective_model = model or cfg["model"]

    previous_str = "\n".join(f"- {t}" for t in previous_topics) if previous_topics else "None yet — this is the first topic!"
    subject_str = "\n".join(f"- {s}" for s in subject_areas) if subject_areas else "- All topics welcome"
    effective_difficulty = target_difficulty or "Intermediate"
    effective_angle = target_angle or TOPIC_ANGLES[0]
    angle_description = _ANGLE_DESCRIPTIONS.get(effective_angle, "")

    prompt = cfg["topic_prompt_template"].format(
        date=date,
        previous_topics=previous_str,
        subject_areas=subject_str,
        target_difficulty=effective_difficulty,
        target_angle=effective_angle,
        angle_description=angle_description,
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


QUIZ_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The MCQ question text"},
                    "option_a": {"type": "string"},
                    "option_b": {"type": "string"},
                    "option_c": {"type": "string"},
                    "option_d": {"type": "string"},
                    "correct": {
                        "type": "string",
                        "enum": ["a", "b", "c", "d"],
                        "description": "The letter of the correct option"
                    },
                    "explanation": {
                        "type": "string",
                        "description": "1-2 sentence explanation of why the correct answer is right"
                    }
                },
                "required": ["question", "option_a", "option_b", "option_c", "option_d", "correct", "explanation"],
                "additionalProperties": False
            }
        }
    },
    "required": ["questions"],
    "additionalProperties": False
}


def generate_quiz(topic_title: str, problem_statement: str, deep_dive: str, model: str = None) -> list[dict]:
    """Generate 5 MCQ quiz questions for a topic using strict structured output."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")

    client = Groq(api_key=api_key)
    cfg = get_llm_config()
    effective_model = model or cfg["model"]

    prompt = (
        f"Generate exactly 5 multiple-choice quiz questions to test understanding of the following system design topic.\n\n"
        f"Topic: {topic_title}\n\n"
        f"Problem: {problem_statement}\n\n"
        f"Technical content: {deep_dive}\n\n"
        "Requirements:\n"
        "- Questions should test conceptual understanding, trade-offs, and real-world application\n"
        "- Each question must have exactly 4 options (A, B, C, D) with only one correct answer\n"
        "- Options should be plausible — avoid obviously wrong distractors\n"
        "- Include a brief explanation for why the correct answer is right\n"
        "- Vary difficulty across the 5 questions"
    )

    logger.info(f"Generating quiz for '{topic_title}' using model {effective_model}")

    response = client.chat.completions.create(
        model=effective_model,
        messages=[
            {"role": "system", "content": cfg["system_prompt"]},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=2048,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "quiz_questions",
                "strict": True,
                "schema": QUIZ_SCHEMA,
            },
        },
    )

    content = response.choices[0].message.content
    data = json.loads(content)
    return data["questions"]
