# 🛡️ CyberMentor

**An AI-powered interactive security learning platform that teaches developers to write secure code — by making them break it first.**

[![Powered by Anthropic Claude](https://img.shields.io/badge/Powered%20by-Anthropic%20Claude-blueviolet)](https://anthropic.com)
[![OWASP Top 10](https://img.shields.io/badge/OWASP-Top%2010%202021-red)](https://owasp.org/Top10/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![React 18](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🎯 The Problem

Security education is broken. Developers sit through 4-hour compliance trainings, forget everything by next sprint, and still push vulnerable code. Traditional courses show you what SQL injection *is* — but never make you feel the danger of writing it yourself.

**The result:** 84% of software vulnerabilities are in application code (Veracode State of Software Security 2024). Junior developers — the ones who most need this knowledge — are the least likely to get meaningful security mentorship.

## 💡 The Solution

CyberMentor flips the script. Instead of passive learning, you get:

1. **Real vulnerable code** — actual patterns from CVEs and OWASP reports
2. **A challenge to exploit it** — understand the attack vector first-hand
3. **Progressive hints** — get unstuck without spoiling the learning moment
4. **AI mentor review** — submit your fix and get line-by-line feedback from Claude
5. **Open-ended chat** — ask anything, your AI security mentor never gets tired

Every interaction is a Socratic dialogue. CyberMentor doesn't just tell you the answer — it guides you to discover *why* the vulnerable pattern is dangerous.

---

## 🚀 Demo

**Try it instantly — no backend required!**

Open `frontend/index.html` directly in your browser. The app includes a full demo mode with embedded challenge data and AI-style explanations.

```bash
# With backend (full AI features):
cd backend
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
uvicorn main:app --reload

# Then open frontend/index.html in your browser
```

### Demo Walkthrough

1. **Browse challenges** — filter by difficulty (Beginner/Intermediate/Advanced) or OWASP category
2. **Pick a challenge** — read the vulnerable code, understand the context
3. **Get hints** — 3 progressive hints that guide without spoiling
4. **Ask for an explanation** — Claude explains the full attack chain with examples
5. **Switch to "Fix It"** — write your secure version in the built-in editor
6. **Submit your fix** — get specific AI feedback on what you got right (and what's still vulnerable)
7. **Chat freely** — ask follow-up questions, explore edge cases, go deep

---

## 🏗 Architecture

```
Browser (React 18 SPA)
      │
      │  REST API calls
      ▼
FastAPI Backend (Python 3.12)
  ├── GET  /api/challenges        → returns challenge catalog
  ├── GET  /api/challenges/{id}   → single challenge detail
  ├── POST /api/mentor/explain    → full vulnerability explanation
  ├── POST /api/mentor/hint       → progressive hint (1–3)
  ├── POST /api/mentor/review-fix → reviews user's fix attempt
  └── POST /api/mentor/chat       → open-ended security chat
      │
      │  Anthropic Messages API
      ▼
Claude (claude-haiku-4-5-20251001)
  Persona: "CyberMentor" — expert AppSec engineer & teacher
  Context: challenge code + OWASP category + user's fix attempt
      │
      ▼
Structured Response (5 sections):
  1. Vulnerability explanation
  2. Attack demonstration
  3. Fix walkthrough
  4. Security principles
  5. Real-world CVE reference
```

---

## 📚 Challenge Library (15 Challenges)

| # | Challenge | OWASP | Difficulty | CVE Example |
|---|-----------|-------|------------|-------------|
| 1 | SQL Injection — Login Bypass | A03 | Beginner | CVE-2023-1234 |
| 2 | Stored XSS — Comment Field | A03 | Beginner | CVE-2021-44228 |
| 3 | IDOR — User Data Access | A01 | Beginner | CVE-2023-20887 |
| 4 | Hardcoded Secrets | A02 | Beginner | — |
| 5 | OS Command Injection | A03 | Intermediate | CVE-2021-41773 |
| 6 | SSRF — Internal Network | A10 | Intermediate | CVE-2019-11510 |
| 7 | Insecure Deserialization | A08 | Intermediate | CVE-2011-2894 |
| 8 | Path Traversal | A01 | Intermediate | CVE-2021-41773 |
| 9 | Weak Cryptography (MD5) | A02 | Intermediate | — |
| 10 | Missing Authentication | A07 | Intermediate | — |
| 11 | Race Condition (TOCTOU) | A04 | Advanced | CVE-2019-1322 |
| 12 | JWT "none" Algorithm | A07 | Advanced | CVE-2015-9235 |
| 13 | Mass Assignment | A04 | Advanced | CVE-2012-5664 |
| 14 | XXE Injection | A05 | Advanced | CVE-2021-44228 |
| 15 | Open Redirect | A01 | Beginner | — |

---

## 📁 Project Structure

```
cybermentor/
├── backend/
│   ├── main.py           ← FastAPI app + AI mentor endpoints
│   ├── challenges.py     ← 15 OWASP challenge definitions
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── index.html        ← Self-contained React 18 SPA (no build step)
├── Dockerfile
├── README.md
└── LICENSE               ← MIT
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | — | Your Anthropic API key |
| `CLAUDE_MODEL` | ❌ | `claude-haiku-4-5-20251001` | Claude model to use |
| `HOST` | ❌ | `0.0.0.0` | Server bind address |
| `PORT` | ❌ | `8000` | Server port |

### Docker

```bash
docker build -t cybermentor .
docker run -e ANTHROPIC_API_KEY=sk-ant-... -p 8000:8000 cybermentor
```

---

## 🤖 AI Mentor Design

The CyberMentor AI persona is carefully engineered for **educational effectiveness**, not just correctness:

**System Prompt Principles:**
- Every explanation follows: *concept → attack demonstration → fix → principle → real-world context*
- Hints are progressively revealing — hint 1 is conceptual, hint 3 is near-direct
- Fix reviews acknowledge what the user got *right* before addressing gaps
- No lecture-style walls of text — structured sections, code examples, concrete takeaways

**Why Haiku?**
`claude-haiku-4-5-20251001` delivers near-instant responses for hints and chat interactions. The snappy feedback loop is critical to learning flow — waiting 5 seconds for a hint breaks immersion. For deeper explanations and fix reviews, the latency is worth it.

---

## 🎓 Educational Philosophy

CyberMentor is built on three principles:

**1. Attack first, defend second**
You can't defend what you don't understand. Every challenge makes you internalize the attack before writing a fix.

**2. Immediate, specific feedback**
Vague feedback kills motivation. When you submit a fix, the AI tells you exactly which line is still vulnerable and why — not "good try, but consider input validation."

**3. Progressive disclosure**
Three-tier hints mean you get to the learning moment at your own pace. Experts skip hints. Beginners use all three. Nobody gets stuck long enough to give up.

---

## 🏆 Built For

**NextDev Hackathon 2026** — targeting *Education + ML/AI* tracks.

Combining:
- **Anthropic Claude** for deep, contextual security mentorship
- **OWASP Top 10** framework — the industry standard for web security
- **Active learning pedagogy** — proven more effective than passive instruction
- **Zero-friction onboarding** — runs entirely in the browser, no account needed

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

*Built by [Soumya Debnath](https://devpost.com/soumyadebnath1619) — NextDev Hackathon 2026*
