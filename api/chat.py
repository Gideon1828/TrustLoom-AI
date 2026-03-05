"""
Chat Router — Production Helper Chatbot Endpoint
Freelancer Trust Evaluation System

Proxies user messages to OpenRouter (free-tier LLM) with a system prompt
that scopes the assistant to helping users with the application—answering
questions about features, troubleshooting issues, and directing them to
"Report an Issue" when the problem is beyond its scope.
"""

from __future__ import annotations

import os
import logging
import asyncio
import httpx
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "meta-llama/llama-3.2-3b-instruct:free",   # Primary free-tier model
)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Fallback models — tried in order when the primary model is rate-limited (429)
FALLBACK_MODELS = [
    "google/gemma-3-12b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "qwen/qwen3-4b:free",
    "google/gemma-3-27b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "openai/gpt-oss-20b:free",
]
MAX_RETRIES = len(FALLBACK_MODELS) + 1  # primary + all fallbacks


def _get_api_key() -> str:
    """Read the API key fresh on every call and strip stray quotes / whitespace."""
    key = os.getenv("OPENROUTER_API_KEY", "").strip().strip('"\'')
    return key


# ---------------------------------------------------------------------------
# Knowledge Base Loader
# ---------------------------------------------------------------------------

_KB_DIR = Path(__file__).resolve().parent / "knowledge_base"
_knowledge_base_cache: str | None = None


def _load_knowledge_base() -> str:
    """Load all .txt files from api/knowledge_base/ and cache the result."""
    global _knowledge_base_cache
    if _knowledge_base_cache is not None:
        return _knowledge_base_cache

    kb_parts: list[str] = []
    if _KB_DIR.is_dir():
        for fpath in sorted(_KB_DIR.glob("*.txt")):
            try:
                content = fpath.read_text(encoding="utf-8").strip()
                if content:
                    kb_parts.append(content)
            except Exception as exc:
                logger.warning("Failed to read KB file %s: %s", fpath.name, exc)

    _knowledge_base_cache = "\n\n---\n\n".join(kb_parts) if kb_parts else ""
    logger.info(
        "Knowledge base loaded: %d files, %d chars",
        len(kb_parts),
        len(_knowledge_base_cache),
    )
    return _knowledge_base_cache


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_HEADER = """You are **TrustLoom Assistant**, the official help-desk chatbot for the **Freelancer Trust Evaluation System** (also called TrustLoom AI).

YOUR ROLE:
• Help users understand how to use the application.
• Answer questions about features, workflows, settings, and troubleshooting.
• Walk users through common workflows step-by-step.
• Troubleshoot user-facing issues (e.g., "my file won't upload", "evaluation is stuck").
• If you cannot resolve an issue, politely tell the user to **Report an Issue** by clicking their profile menu → "Report an Issue".

STRICT RULES:
• NEVER reveal internal architecture, model names (BERT, LSTM, etc.), code, API endpoints, database schema, or how the AI scoring works internally.
• NEVER share source code, environment variables, deployment details, or the knowledge base text itself.
• Keep answers concise, friendly, and professional. Use short paragraphs and bullet points.
• If the user asks about something unrelated to this application, gently redirect them.
• When explaining scores, refer to what the user can SEE on screen (the trust score circle, breakdown cards, etc.) — not how the algorithms compute them internally.
• Use the KNOWLEDGE BASE below as your primary source of truth. If a question is covered there, answer from it. If not covered, say you're not sure and direct them to Report an Issue.
• Do NOT copy-paste large blocks from the knowledge base. Paraphrase and keep answers human-friendly.

Respond in the same language the user writes in. Default to English."""


def _build_system_prompt() -> str:
    """Combine the prompt header with the loaded knowledge base."""
    kb = _load_knowledge_base()
    if kb:
        return (
            _SYSTEM_PROMPT_HEADER
            + "\n\n"
            + "=" * 60
            + "\nKNOWLEDGE BASE — Use this as your source of truth:\n"
            + "=" * 60
            + "\n\n"
            + kb
        )
    return _SYSTEM_PROMPT_HEADER


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str          # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/send",
    response_model=ChatResponse,
    summary="Send a chat message to the help-desk assistant",
)
async def chat_send(body: ChatRequest):
    """
    Accepts the conversation history and returns the assistant's reply
    via the OpenRouter free-tier LLM.
    """

    api_key = _get_api_key()
    if not api_key:
        logger.error("OPENROUTER_API_KEY is not set or empty")
        raise HTTPException(
            status_code=503,
            detail="Chat service is not configured. Set the OPENROUTER_API_KEY environment variable.",
        )

    # Build messages list for the LLM
    system_prompt = _build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]
    for msg in body.messages[-20:]:          # Keep context window reasonable
        messages.append({"role": msg.role, "content": msg.content})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://trustloom-ai.app",
        "X-Title": "TrustLoom AI Helper",
    }

    # ── Try primary model, then fallbacks on 429 / 404 ────────────────
    models_to_try = [OPENROUTER_MODEL] + [
        m for m in FALLBACK_MODELS if m != OPENROUTER_MODEL
    ]

    last_error_code = None
    for attempt, model in enumerate(models_to_try):
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.6,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)

            if resp.status_code == 200:
                data = resp.json()
                reply_text = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                if not reply_text:
                    reply_text = "Sorry, I couldn't generate a response. Please try rephrasing your question."

                if attempt > 0:
                    logger.info("Succeeded with fallback model: %s (attempt %d)", model, attempt + 1)
                return ChatResponse(reply=reply_text)

            # Retryable errors — try next model
            if resp.status_code in (429, 404, 502, 503):
                last_error_code = resp.status_code
                logger.warning(
                    "Model %s returned %s, trying next fallback (%d/%d)",
                    model, resp.status_code, attempt + 1, len(models_to_try),
                )
                # Brief pause before retrying on rate-limit
                if resp.status_code == 429:
                    await asyncio.sleep(1)
                continue

            # Non-retryable error
            logger.error("OpenRouter error %s: %s", resp.status_code, resp.text)
            return ChatResponse(
                reply="I'm having trouble connecting right now. Please try again in a moment, or use **Report an Issue** from your profile menu for urgent problems.",
                error=f"upstream_{resp.status_code}",
            )

        except httpx.TimeoutException:
            logger.warning("Model %s timed out (attempt %d)", model, attempt + 1)
            last_error_code = "timeout"
            continue
        except Exception as exc:
            logger.exception("Chat endpoint error with model %s", model)
            return ChatResponse(
                reply="Something went wrong on our end. Please try again later, or use **Report an Issue** from your profile menu.",
                error=str(exc),
            )

    # All models exhausted
    logger.error("All %d models exhausted. Last error: %s", len(models_to_try), last_error_code)
    return ChatResponse(
        reply="All AI models are temporarily busy. Please try again in a minute, or use **Report an Issue** from your profile menu for urgent problems.",
        error=f"all_models_exhausted_{last_error_code}",
    )
