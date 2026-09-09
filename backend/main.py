"""
CyberMentor — FastAPI Backend

AI-powered security education API using Anthropic Claude.
"""

from __future__ import annotations
import os
from contextlib import asynccontextmanager
from typing import Literal

import anthropic
import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.challenges import CHALLENGES, get_challenge, get_challenges_by_difficulty

logger = structlog.get_logger(__name__)

# ─── Anthropic client ─────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

MENTOR_SYSTEM_PROMPT = """You are CyberMentor — a friendly, expert application security teacher
who makes complex security concepts click for developers of all levels.

Your teaching style:
- Use clear, practical explanations with real examples
- For BEGINNERS: use analogies, avoid jargon, be encouraging
- For INTERMEDIATE: explain the "why", show real CVEs, discuss attack patterns
- For ADVANCED: deep-dive into exploitation techniques, mitigations, defense-in-depth

Always structure your responses with:
1. 🎯 **The Core Issue** — what's wrong in plain English
2. 🔥 **How It's Exploited** — concrete attack scenario with example payload
3. 🛡️ **The Fix** — exact, copy-paste-ready secure code
4. 🧠 **Why It Works** — the security principle that prevents the attack
5. 🌍 **Real World** — mention a real CVE or breach if relevant

Keep responses focused and actionable. Use code blocks for all code."""


# ─── Request/Response models ──────────────────────────────────────────────────
class ExplainRequest(BaseModel):
    challenge_id: str
    user_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    specific_question: str | None = None

class HintRequest(BaseModel):
    challenge_id: str
    hint_number: int = 0

class ReviewFixRequest(BaseModel):
    challenge_id: str
    user_fix: str
    language: str = "python"

class ChatRequest(BaseModel):
    message: str
    challenge_id: str | None = None
    history: list[dict] = []

# ─── App lifecycle ────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CyberMentor API starting", challenges=len(CHALLENGES))
    yield
    logger.info("CyberMentor API stopping")

app = FastAPI(
    title="CyberMentor API",
    description="AI-powered security education powered by Anthropic Claude",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Challenge endpoints ──────────────────────────────────────────────────────
@app.get("/api/challenges")
def list_challenges(difficulty: str | None = None):
    """Return all challenges, optionally filtered by difficulty."""
    challenges = get_challenges_by_difficulty(difficulty) if difficulty else CHALLENGES
    return [
        {
            "id": c.id,
            "title": c.title,
            "owasp_id": c.owasp_id,
            "owasp_name": c.owasp_name,
            "difficulty": c.difficulty,
            "language": c.language,
            "description": c.description,
            "vulnerable_code": c.vulnerable_code,
            "tags": c.tags,
            "cve_example": c.cve_example,
            "hint_count": len(c.hints),
        }
        for c in challenges
    ]

@app.get("/api/challenges/{challenge_id}")
def get_challenge_detail(challenge_id: str):
    """Return a single challenge by ID."""
    challenge = get_challenge(challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return {
        "id": challenge.id,
        "title": challenge.title,
        "owasp_id": challenge.owasp_id,
        "owasp_name": challenge.owasp_name,
        "difficulty": challenge.difficulty,
        "language": challenge.language,
        "description": challenge.description,
        "vulnerable_code": challenge.vulnerable_code,
        "tags": challenge.tags,
        "cve_example": challenge.cve_example,
        "hint_count": len(challenge.hints),
    }

# ─── AI Mentor endpoints ──────────────────────────────────────────────────────
@app.post("/api/mentor/explain")
def explain_vulnerability(req: ExplainRequest):
    """Get a full AI explanation of a challenge's vulnerability."""
    challenge = get_challenge(req.challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    user_prompt = f"""Teach me about this security vulnerability at a {req.user_level} level.

**Challenge**: {challenge.title}
**OWASP Category**: {challenge.owasp_id} — {challenge.owasp_name}

**Vulnerable Code** ({challenge.language}):
```{challenge.language}
{challenge.vulnerable_code}
```

**Context**: {challenge.description}
"""
    if req.specific_question:
        user_prompt += f"\n**My specific question**: {req.specific_question}"

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=MENTOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return {"explanation": message.content[0].text, "tokens_used": message.usage.output_tokens}

@app.post("/api/mentor/hint")
def get_hint(req: HintRequest):
    """Get a progressive hint for a challenge."""
    challenge = get_challenge(req.challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    hint_idx = min(req.hint_number, len(challenge.hints) - 1)
    hint_text = challenge.hints[hint_idx]

    return {
        "hint": hint_text,
        "hint_number": hint_idx,
        "hints_remaining": len(challenge.hints) - hint_idx - 1,
    }

@app.post("/api/mentor/review-fix")
def review_fix(req: ReviewFixRequest):
    """AI review of the user's proposed fix for a vulnerability."""
    challenge = get_challenge(req.challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    user_prompt = f"""A developer is trying to fix a security vulnerability. Review their fix.

**Original Vulnerability** ({challenge.owasp_id} — {challenge.owasp_name}):
```{challenge.language}
{challenge.vulnerable_code}
```

**Developer's proposed fix**:
```{req.language}
{req.user_fix}
```

Evaluate:
1. ✅ Does this fix actually solve the vulnerability? (Yes/Partial/No)
2. 🔍 What did they get right?
3. ⚠️ What's still missing or could be improved?
4. 🛡️ Show the ideal fix with explanation

Be encouraging — learning from mistakes is how security knowledge grows!"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=MENTOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return {"review": message.content[0].text}

@app.post("/api/mentor/chat")
def chat_with_mentor(req: ChatRequest):
    """Open-ended chat with the AI security mentor."""
    context = ""
    if req.challenge_id:
        challenge = get_challenge(req.challenge_id)
        if challenge:
            context = f"The user is currently working on the challenge: '{challenge.title}' ({challenge.owasp_id} — {challenge.owasp_name}).\n"

    messages = req.history[-6:] + [{"role": "user", "content": req.message}]

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=MENTOR_SYSTEM_PROMPT + ("\n\nContext: " + context if context else ""),
        messages=messages,
    )
    return {"reply": message.content[0].text}

@app.get("/health")
def health():
    return {"status": "ok", "service": "cybermentor-api", "version": "1.0.0", "challenges": len(CHALLENGES)}
