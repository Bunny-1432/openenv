"""
Inference Script — Email Triage Environment
============================================
MANDATORY environment variables:
    API_BASE_URL      The API endpoint for the LLM.
    MODEL_NAME        The model identifier to use for inference.
    HF_TOKEN          Your Hugging Face / API key.
    LOCAL_IMAGE_NAME  (Optional) Local Docker image name when using from_docker_image().
    EMAIL_ENV_URL     (Optional) Running server URL (default: http://localhost:8000).

Defaults are set only for API_BASE_URL and MODEL_NAME:
    API_BASE_URL = os.getenv("API_BASE_URL", "<your-active-endpoint>")
    MODEL_NAME   = os.getenv("MODEL_NAME",   "<your-active-model>")

STDOUT FORMAT (strictly followed):
    [START] task=<task_name> env=email_triage_env model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

Rules:
  - One [START] line at episode begin.
  - One [STEP] line per step, immediately after env.step() returns.
  - One [END] line after env.close(), always emitted (even on exception).
  - reward and rewards are formatted to 2 decimal places.
  - done and success are lowercase booleans: true or false.
  - error is the raw error string, or null if none.
  - All fields on a single line with no newlines within a line.
  - Each task returns score in [0, 1].
"""

import asyncio
import json
import os
import textwrap
from typing import List, Optional

from openai import OpenAI

from client import EmailTriageEnv

# ── Mandatory environment variables ──────────────────────────────────────────
# Defaults are set ONLY for API_BASE_URL and MODEL_NAME (per spec).
API_BASE_URL     = os.getenv("API_BASE_URL", "<your-active-endpoint>")
MODEL_NAME       = os.getenv("MODEL_NAME",   "<your-active-model>")
HF_TOKEN         = os.getenv("HF_TOKEN")           # No default — must be set
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")   # Optional: use docker image

# Secondary config
ENV_URL           = os.getenv("EMAIL_ENV_URL", "http://localhost:8000")
BENCHMARK         = "email_triage_env"
TASKS             = ["classify_email", "triage_inbox", "draft_reply"]
MAX_STEPS         = 8
TEMPERATURE       = 0.3
MAX_TOKENS        = 512
SUCCESS_THRESHOLD = 0.5  # score ≥ 0.5 → success=true

# ── Structured log helpers ────────────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val  = str(done).lower()
    # Sanitise — no newlines on a single log line
    action_safe = action.replace("\n", " ").replace("\r", "")[:200]
    print(
        f"[STEP] step={step} action={action_safe} "
        f"reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert email management assistant operating in an OpenEnv environment.
    You interact with the environment by calling MCP tools.

    Available tools (respond with a single JSON tool call):
      get_email(email_id)                                → read full email content
      list_emails()                                      → list current episode emails
      classify_email(email_id, category)                 → Task 1: submit classification
      set_email_priority(email_id, priority, labels)     → Task 2: triage + label
      submit_reply(email_id, reply_text)                 → Task 3: draft & submit reply
      get_task_status()                                  → check current score

    Valid categories: urgent, spam, newsletter, support, meeting, security, general

    Strategy:
      1. Call get_task_status() to understand the current task.
      2. Read relevant emails with get_email() or list_emails().
      3. Submit your answer with the appropriate action tool.

    Respond with ONLY a JSON object like:
    {"name": "<tool_name>", "arguments": {"arg1": "value1"}}
""").strip()


def build_prompt(task_name: str, step: int, last_obs: str, history: List[str]) -> str:
    hist = "\n".join(history[-6:]) if history else "None"
    return textwrap.dedent(f"""
        Task: {task_name}  |  Step: {step}/{MAX_STEPS}

        Last environment response:
        {last_obs}

        Recent history:
        {hist}

        What tool do you call next? Reply with a single JSON tool call.
    """).strip()


# ── Model call (OpenAI client — uses API_BASE_URL, MODEL_NAME, HF_TOKEN) ─────

def get_tool_call(
    client: OpenAI,
    task_name: str,
    step: int,
    last_obs: str,
    history: List[str],
) -> dict:
    """Ask the model for the next tool call. Returns {'name': ..., 'arguments': ...}."""
    prompt = build_prompt(task_name, step, last_obs, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        parsed = json.loads(text)
        if "name" in parsed and "arguments" in parsed:
            return parsed
        return {"name": "get_task_status", "arguments": {}}
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return {"name": "get_task_status", "arguments": {}}


# ── Single task episode ───────────────────────────────────────────────────────

async def run_task(client: OpenAI, env: EmailTriageEnv, task_name: str) -> dict:
    """
    Run one task episode. Returns result dict:
      {task, success, steps, score, rewards}
    Always emits [START] … [STEP]* … [END].
    """
    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    rewards:     List[float] = []
    steps_taken: int         = 0
    score:       float       = 0.0
    success:     bool        = False

    try:
        # ── Reset ──────────────────────────────────────────────────────────
        reset_result = await env.reset(task_name=task_name)
        # Extract task briefing from metadata
        if hasattr(reset_result, "observation"):
            meta     = reset_result.observation.metadata or {}
            last_obs = meta.get("message", "Episode reset. Call get_task_status().")
        else:
            last_obs = str(reset_result)

        done    = False
        history: List[str] = []

        # ── Step loop ──────────────────────────────────────────────────────
        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            # Get next tool call from model
            tool_call  = get_tool_call(client, task_name, step, last_obs, history)
            tool_name  = tool_call.get("name",      "get_task_status")
            tool_args  = tool_call.get("arguments", {})
            action_str = f"{tool_name}({json.dumps(tool_args)})"

            error_msg: Optional[str] = None
            reward: float = 0.0

            try:
                # Execute the tool against the environment
                result   = await env.call_tool(tool_name, **tool_args)
                last_obs = str(result)
                done     = (
                    "Episode complete" in last_obs
                    or "episode ended" in last_obs.lower()
                )
            except Exception as exc:
                error_msg = str(exc)[:120]
                last_obs  = f"Error: {error_msg}"
                done      = False

            rewards.append(reward)
            steps_taken = step
            history.append(f"Step {step}: {action_str} → {last_obs[:100]}")

            log_step(step=step, action=action_str, reward=reward, done=done, error=error_msg)

        # ── Final score from environment ───────────────────────────────────
        try:
            status_raw = await env.call_tool("get_task_status")
            status     = json.loads(str(status_raw))
            score      = float(status.get("cumulative_score", 0.0))
        except Exception:
            score = max(rewards) if rewards else 0.0

        score   = max(0.01, min(0.99, score))
        success = score >= SUCCESS_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task '{task_name}' error: {exc}", flush=True)
        score   = 0.0
        success = False

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {
        "task":    task_name,
        "success": success,
        "steps":   steps_taken,
        "score":   score,
        "rewards": rewards,
    }


# ── Main (async) ──────────────────────────────────────────────────────────────

async def main() -> None:
    # All LLM calls use the OpenAI client configured via the mandatory variables
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    # Connect to the environment:
    #   - If LOCAL_IMAGE_NAME is set → spin up a local Docker container
    #   - Otherwise → connect to a running server at ENV_URL
    if LOCAL_IMAGE_NAME:
        env = await EmailTriageEnv.from_docker_image(LOCAL_IMAGE_NAME)
    else:
        env = EmailTriageEnv(base_url=ENV_URL)

    all_results = []

    try:
        for task_name in TASKS:
            result = await run_task(client, env, task_name)
            all_results.append(result)
    finally:
        try:
            await env.close()
        except Exception as exc:
            print(f"[DEBUG] env.close() error: {exc}", flush=True)

    # Summary (informational, not part of mandatory format)
    print("\n[SUMMARY]", flush=True)
    for r in all_results:
        print(
            f"  task={r['task']} success={str(r['success']).lower()} "
            f"score={r['score']:.2f} steps={r['steps']}",
            flush=True,
        )
    avg = sum(r["score"] for r in all_results) / len(all_results) if all_results else 0.0
    print(f"  average_score={avg:.2f}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
