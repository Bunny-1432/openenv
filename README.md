---
title: Email Triage Environment
emoji: 📧
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
tags:
  - openenv
  - rl
  - agent
  - email
  - triage
license: apache-2.0
---

# 📧 Email Triage Environment

> **OpenEnv** | Real-world agentic email management environment for RL training and agent evaluation.

An agentic execution environment where an AI agent manages a realistic email inbox — classifying messages, prioritizing batches by urgency, and drafting professional replies. Knowledge workers spend 2–4 hours per day on email; this environment turns that into a concrete, measurable benchmark.

## Why Email Triage?

| Criterion | This Environment |
|---|---|
| Real-world task | ✅ Universal human task, measurable at scale |
| Partial progress signal | ✅ Dense rewards at each tool call |
| Difficulty progression | ✅ Easy → Medium → Hard |
| Deterministic graders | ✅ Reproducible scoring across runs |
| Novel domain | ✅ No prior OpenEnv email environment |

---

## Environment Overview

### Action Space

Actions are **MCP tool calls** — the agent calls tools by name with typed arguments:

| Tool | Arguments | Purpose |
|---|---|---|
| `get_email` | `email_id: str` | Read full email content |
| `list_emails` | *(none)* | List emails in current episode |
| `classify_email` | `email_id, category` | Task 1: submit classification |
| `set_email_priority` | `email_id, priority, labels` | Task 2: triage + label email |
| `submit_reply` | `email_id, reply_text` | Task 3: submit drafted reply |
| `get_task_status` | *(none)* | Check score and remaining steps |

### Observation Space

Each tool call returns a string response with:
- Email content (body, subject, sender, timestamp)
- Feedback on the last action
- Running score
- Episode completion signal

### Reward Function

Rewards are **dense** — the agent receives partial credit throughout each episode:

| Task | Reward Signal |
|---|---|
| `classify_email` | 1.0 correct, 0.3 related category, 0.0 wrong |
| `triage_inbox` | Spearman rank correlation (priorities) + label F1, updated per email |
| `draft_reply` | Tone (30%) + Coverage (40%) + Length (20%) + Structure (10%) |

---

## Tasks

### Task 1 — `classify_email` (Easy)
- **Objective**: Read a single email and classify it into one of 7 categories
- **Categories**: `urgent`, `spam`, `newsletter`, `support`, `meeting`, `security`, `general`
- **Max steps**: 6
- **Baseline score**: ~0.40 (random = 0.14)

### Task 2 — `triage_inbox` (Medium)
- **Objective**: Assign priority (1–5) and category labels to all 5 emails in a batch
- **Grader**: Weighted combination of Spearman rank correlation + label accuracy
- **Max steps**: 15
- **Baseline score**: ~0.35

### Task 3 — `draft_reply` (Hard)
- **Objective**: Read an important email and draft a professional, complete reply
- **Grader**: NLP heuristics on tone, keyword coverage, length, and structure
- **Max steps**: 8
- **Baseline score**: ~0.30

---

## Setup

### Quick Start (Local)

```bash
# 1. Install dependencies
pip install openenv-core fastmcp uvicorn pydantic openai

# 2. Start server
uvicorn server.app:app --host 0.0.0.0 --port 8000

# 3. Test in another terminal
curl http://localhost:8000/health
curl -X POST http://localhost:8000/reset -H "Content-Type: application/json" -d "{}"
```

### Docker

```bash
docker build -t email-triage-env .
docker run -p 8000:8000 email-triage-env
```

### Run Baseline Inference

```bash
export HF_TOKEN=your_hf_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export EMAIL_ENV_URL=http://localhost:8000

python inference.py
```

Expected output format:
```
[START] task=classify_email env=email_triage_env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=get_task_status({}) reward=0.00 done=false error=null
[STEP] step=2 action=get_email({"email_id": "e001"}) reward=0.00 done=false error=null
[STEP] step=3 action=classify_email({"email_id": "e001", "category": "urgent"}) reward=1.00 done=true error=null
[END] success=true steps=3 score=1.000 rewards=0.00,0.00,1.00
```

### Use as Python Client

```python
from client import EmailTriageEnv

with EmailTriageEnv(base_url="http://localhost:8000").sync() as env:
    # Reset and get task briefing
    result = env.reset(task_name="classify_email")
    
    # Read an email
    content = env.call_tool("get_email", email_id="e001")
    print(content)
    
    # Classify it
    feedback = env.call_tool("classify_email", email_id="e001", category="urgent")
    print(feedback)
```

---

## Project Structure

```
email_triage_env/
├── openenv.yaml              # OpenEnv manifest
├── pyproject.toml            # Python dependencies
├── Dockerfile                # Container build
├── README.md                 # This file
├── models.py                 # Pydantic Action/Observation models
├── client.py                 # EmailTriageEnv client
├── inference.py              # Baseline inference script
└── server/
    ├── __init__.py
    ├── app.py                # FastAPI application
    ├── email_environment.py  # MCPEnvironment implementation
    ├── email_data.py         # Synthetic email dataset (seed=42)
    └── tasks.py              # Task definitions + graders
```

---

## Baseline Scores

Model: `Qwen/Qwen2.5-72B-Instruct` via HuggingFace Router

| Task | Difficulty | Baseline Score |
|---|---|---|
| `classify_email` | Easy | ~0.40 |
| `triage_inbox` | Medium | ~0.35 |
| `draft_reply` | Hard | ~0.30 |
| **Average** | | **~0.35** |

*Scores are deterministic across runs given the same model and seed.*

---

## OpenEnv Spec Compliance

- ✅ `spec_version: 1` in `openenv.yaml`
- ✅ `reset()` → fresh episode with task briefing
- ✅ `step()` / `step_async()` → observation + reward + done
- ✅ `state` property → episode_id + step_count  
- ✅ Typed Pydantic `Action` and `Observation` models
- ✅ MCP tool interface (FastMCP + MCPEnvironment)
- ✅ `create_app()` factory for HTTP/WebSocket server
- ✅ Dockerfile builds and runs cleanly
- ✅ `openenv validate` passes

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HF_TOKEN` | *(required)* | Hugging Face / API key |
| `API_BASE_URL` | `https://router.huggingface.co/v1` | LLM endpoint |
| `MODEL_NAME` | `Qwen/Qwen2.5-72B-Instruct` | Model identifier |
| `EMAIL_ENV_URL` | `http://localhost:8000` | Environment server URL |
| `ENABLE_WEB_INTERFACE` | `true` | Enable built-in web UI |

---

## License

Apache 2.0
