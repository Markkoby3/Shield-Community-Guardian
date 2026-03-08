import re
import logging
from operator import itemgetter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.core.config import get_settings
from backend.models import DigestContent
from backend.services.fallbacks import get_fallback

logger = logging.getLogger(__name__)

_retriever = None
_chain = None

SYSTEM_PROMPT = """You are a calm, empowering community safety assistant.
A resident has received the following {category} alert. Using the safety context below, respond with:

SUMMARY: One calm sentence explaining what happened.
STEPS:
1. First empowering action the resident can take right now.
2. Second protective step they should take within 24 hours.
3. Third longer-term step to stay safe.

Be specific to the alert type. Do not cause unnecessary alarm. Keep each step under 20 words.

Context:
{context}

Alert: {question}"""


def init_rag() -> None:
    """Build and cache the RAG chain. Called once at startup."""
    global _retriever, _chain
    settings = get_settings()

    with open(settings.security_docs_path) as f:
        docs = [d.strip() for d in f.read().split("\n\n") if d.strip()]

    api_key = settings.openai_api_key
    db = Chroma.from_texts(docs, OpenAIEmbeddings(openai_api_key=api_key))
    _retriever = db.as_retriever()

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=api_key)

    _chain = (
        {
            "context": itemgetter("question") | _retriever,
            "question": itemgetter("question"),
            "category": itemgetter("category"),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    logger.info("RAG chain initialized with %d document chunks", len(docs))


def generate_digest(alert: str, category: str = "general") -> tuple[DigestContent, str]:
    """
    Returns (DigestContent, method) where method is 'AI' or 'fallback'.
    Never raises — falls back gracefully if RAG is unavailable.
    """
    if _chain is None:
        logger.warning("RAG chain not initialized, using fallback")
        return get_fallback(category), "fallback"

    try:
        raw = _chain.invoke({"question": alert, "category": category})
        digest = _parse_digest(raw.strip())
        return digest, "AI"
    except Exception as e:
        logger.error("RAG generation failed: %s", e, exc_info=True)
        return get_fallback(category), "fallback"


def _parse_digest(raw: str) -> DigestContent:
    """Parse SUMMARY + STEPS format into DigestContent."""
    summary = ""
    steps = []

    summary_match = re.search(r"SUMMARY:\s*(.+?)(?=\nSTEPS:|\Z)", raw, re.DOTALL | re.IGNORECASE)
    if summary_match:
        summary = summary_match.group(1).strip()

    steps_match = re.search(r"STEPS:\s*(.+)", raw, re.DOTALL | re.IGNORECASE)
    if steps_match:
        raw_steps = steps_match.group(1).strip()
        steps = [
            re.sub(r"^\d+[\.\)]\s*", "", line).strip()
            for line in raw_steps.splitlines()
            if re.match(r"^\d", line.strip())
        ]

    if not summary:
        summary = raw.split("\n")[0].strip()
    if not steps:
        steps = ["Please follow guidance from official local safety sources."]

    return DigestContent(summary=summary, steps=steps)
