"""
Email Triage Environment — MCPEnvironment implementation.

Exposes 3 tasks as MCP tools that an agent can call:
  - get_email        : read an email
  - list_emails      : list available emails
  - classify_email   : submit a classification (Task 1)
  - set_email_priority: set priority + labels (Task 2)
  - submit_reply     : submit a drafted reply (Task 3)
  - get_task_status  : check current score
"""

from __future__ import annotations

import json
import random
from typing import Any, Optional
from uuid import uuid4

from fastmcp import FastMCP
from openenv.core.env_server.mcp_environment import MCPEnvironment
from openenv.core.env_server.types import Observation, State

from server.email_data import EMAIL_BY_ID, EMAILS, TASK_EMAIL_GROUPS
from server.tasks import (
    TASKS,
    _clamp,
    grade_classify,
    grade_reply,
    grade_triage,
)


class EmailTriageEnvironment(MCPEnvironment):
    """
    Email Triage agentic environment.

    Simulates a real-world inbox management task. The agent must classify,
    prioritize, and respond to realistic synthetic emails.

    Three tasks of increasing difficulty:
      - classify_email (easy)
      - triage_inbox   (medium)
      - draft_reply    (hard)

    All task interactions happen through MCP tool calls.
    """

    def __init__(self) -> None:
        mcp = FastMCP("email_triage_env")
        self._setup_tools(mcp)
        super().__init__(mcp)

        # Episode state (reset on each reset() call)
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._task_name: str = "classify_email"
        self._task_index: int = 0          # which email / batch in the task
        self._episode_index: int = 0       # global count — drives task rotation
        self._batch_ids: list[str] = []
        self._current_email_id: str = ""
        self._cumulative_score: float = 0.0
        self._done: bool = False
        self._triage_submissions: dict[str, dict] = {}
        self._read_email_ids: set[str] = set()
        self._step_rewards: list[float] = []
        self._max_steps: int = 8

    # ────────────────────────────────────────────────────────────────────────
    # Tool definitions
    # ────────────────────────────────────────────────────────────────────────

    def _setup_tools(self, mcp: FastMCP) -> None:
        env = self  # capture reference

        @mcp.tool
        def get_email(email_id: str) -> str:
            """
            Read the full content of an email.

            Args:
                email_id: The ID of the email to read (e.g. 'e001')

            Returns:
                JSON string with the email fields: id, subject, sender, timestamp, body
            """
            email = EMAIL_BY_ID.get(email_id)
            if email is None:
                return json.dumps({"error": f"Email '{email_id}' not found."})
            env._read_email_ids.add(email_id)
            env._state.step_count += 1
            out = {k: email[k] for k in ("id", "subject", "sender", "sender_name", "timestamp", "body")}
            return json.dumps(out, indent=2)

        @mcp.tool
        def list_emails() -> str:
            """
            List all emails available in the current episode.

            Returns:
                JSON array with each email's id, subject, sender, and timestamp
            """
            env._state.step_count += 1
            ids = env._batch_ids if env._batch_ids else (
                [env._current_email_id] if env._current_email_id else []
            )
            summaries = []
            for eid in ids:
                e = EMAIL_BY_ID.get(eid, {})
                summaries.append({
                    "id": e.get("id", eid),
                    "subject": e.get("subject", ""),
                    "sender": e.get("sender_name", e.get("sender", "")),
                    "timestamp": e.get("timestamp", ""),
                })
            return json.dumps(summaries, indent=2)

        @mcp.tool
        def classify_email(email_id: str, category: str) -> str:
            """
            Submit your classification for an email (Task 1: classify_email).

            Args:
                email_id: The ID of the email to classify
                category: One of: urgent, spam, newsletter, support, meeting, security, general

            Returns:
                Feedback string with your score and the correct answer
            """
            if env._done:
                return "Episode already ended. Call reset() to start a new episode."
            if env._task_name != "classify_email":
                return f"classify_email is not the active task. Current task: {env._task_name}"

            valid_cats = ["urgent", "spam", "newsletter", "support", "meeting", "security", "general"]
            cat_clean = category.strip().lower()
            if cat_clean not in valid_cats:
                return (
                    f"Invalid category '{category}'. Must be one of: "
                    + ", ".join(valid_cats)
                )

            read_first = email_id in env._read_email_ids
            score = grade_classify(email_id, cat_clean, read_first)
            env._cumulative_score = score
            env._step_rewards.append(score)
            env._done = True
            env._state.step_count += 1

            correct = EMAIL_BY_ID.get(email_id, {}).get("category", "?")
            if score >= _clamp(1.0):
                return (
                    f"✓ Correct! Category '{cat_clean}' is right. Score: {score:.2f}\n"
                    f"Episode complete."
                )
            elif score > _clamp(0.0):
                return (
                    f"✗ Partially correct. You said '{cat_clean}', correct was '{correct}'. "
                    f"Related category gets partial credit. Score: {score:.2f}\nEpisode complete."
                )
            else:
                return (
                    f"✗ Incorrect. You said '{cat_clean}', correct was '{correct}'. Score: {score:.2f}\n"
                    f"Episode complete."
                )

        @mcp.tool
        def set_email_priority(email_id: str, priority: int, labels: str) -> str:
            """
            Assign a priority and labels to an email (Task 2: triage_inbox).

            Args:
                email_id: The ID of the email to triage
                priority: Priority level 1 (most urgent) to 5 (least urgent)
                labels: Comma-separated category labels, e.g. 'urgent,support'

            Returns:
                Feedback on this email's triage; overall score when all emails done
            """
            if env._done:
                return "Episode already ended. Call reset() to start a new episode."
            if env._task_name != "triage_inbox":
                return f"set_email_priority is not active. Current task: {env._task_name}"
            if email_id not in env._batch_ids:
                return f"Email '{email_id}' is not in the current batch: {env._batch_ids}"
            if not (1 <= priority <= 5):
                return "Priority must be between 1 and 5."

            label_list = [l.strip().lower() for l in labels.split(",") if l.strip()]
            env._triage_submissions[email_id] = {"priority": priority, "labels": label_list}
            env._state.step_count += 1

            # Intermediate partial reward
            partial_score = grade_triage(env._triage_submissions, env._batch_ids)
            env._step_rewards.append(partial_score)
            env._cumulative_score = partial_score

            triaged = len(env._triage_submissions)
            total = len(env._batch_ids)

            if triaged >= total:
                env._done = True
                return (
                    f"✓ All {total} emails triaged. Final score: {partial_score:.2f}\n"
                    f"Episode complete."
                )
            return (
                f"Set priority={priority}, labels={label_list} for {email_id}. "
                f"({triaged}/{total} emails done) Running score: {partial_score:.2f}"
            )

        @mcp.tool
        def submit_reply(email_id: str, reply_text: str) -> str:
            """
            Submit a drafted reply to an email (Task 3: draft_reply).

            Args:
                email_id: The ID of the email you are replying to
                reply_text: The full reply text to send (50-400 words recommended)

            Returns:
                Detailed scoring breakdown and feedback
            """
            if env._done:
                return "Episode already ended. Call reset() to start a new episode."
            if env._task_name != "draft_reply":
                return f"submit_reply is not active. Current task: {env._task_name}"
            if not reply_text or not reply_text.strip():
                return "reply_text cannot be empty."

            score = grade_reply(email_id, reply_text)
            env._cumulative_score = score
            env._step_rewards.append(score)
            env._done = True
            env._state.step_count += 1

            words = len(reply_text.split())
            feedback = (
                f"Reply submitted ({words} words). Score: {score:.2f}\n"
                f"Tip — grading weights: tone 30%, coverage 40%, length 20%, structure 10%.\n"
                f"Episode complete."
            )
            return feedback

        @mcp.tool
        def get_task_status() -> str:
            """
            Get the current task name, description, score, and remaining steps.

            Returns:
                JSON string with task status information
            """
            env._state.step_count += 1
            task_def = TASKS.get(env._task_name, {})
            status = {
                "task_name": env._task_name,
                "difficulty": task_def.get("difficulty", "unknown"),
                "cumulative_score": round(env._cumulative_score, 4),
                "steps_taken": env._state.step_count,
                "max_steps": env._max_steps,
                "done": env._done,
                "description": task_def.get("description", ""),
            }
            return json.dumps(status, indent=2)

    # ────────────────────────────────────────────────────────────────────────
    # OpenEnv lifecycle
    # ────────────────────────────────────────────────────────────────────────

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        task_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Observation:
        """
        Reset the environment and start a new episode.

        Rotates through tasks: classify_email → triage_inbox → draft_reply → repeat.

        Args:
            seed: Optional random seed
            episode_id: Optional episode ID
            task_name: Force a specific task ('classify_email', 'triage_inbox', 'draft_reply')

        Returns:
            Observation with task description and initial email context
        """
        rng = random.Random(seed if seed is not None else self._episode_index)

        # Task rotation (or forced)
        task_order = ["classify_email", "triage_inbox", "draft_reply"]
        if task_name and task_name in TASKS:
            self._task_name = task_name
        else:
            self._task_name = task_order[self._episode_index % 3]

        self._episode_index += 1
        self._state = State(episode_id=episode_id or str(uuid4()), step_count=0)
        self._cumulative_score = 0.0
        self._done = False
        self._triage_submissions = {}
        self._read_email_ids = set()
        self._step_rewards = []
        self._batch_ids = []
        self._current_email_id = ""

        task_def = TASKS[self._task_name]
        self._max_steps = task_def["max_steps"]

        # Set up email(s) for this task
        if self._task_name == "classify_email":
            email_ids = task_def["email_ids"]
            self._current_email_id = rng.choice(email_ids)
            email = EMAIL_BY_ID[self._current_email_id]
            context = (
                f"Email to classify:\n"
                f"  ID: {self._current_email_id}\n"
                f"  From: {email['sender_name']} <{email['sender']}>\n"
                f"  Subject: {email['subject']}\n"
                f"  (Use get_email('{self._current_email_id}') to read the full body)"
            )
            self._batch_ids = [self._current_email_id]

        elif self._task_name == "triage_inbox":
            batches = task_def["email_batches"]
            self._batch_ids = batches[self._episode_index % len(batches)]
            context_lines = []
            for eid in self._batch_ids:
                e = EMAIL_BY_ID[eid]
                context_lines.append(
                    f"  [{eid}] From: {e['sender_name']} | Subject: {e['subject']}"
                )
            context = "Inbox batch (5 emails to triage):\n" + "\n".join(context_lines)

        else:  # draft_reply
            email_ids = task_def["email_ids"]
            self._current_email_id = rng.choice(email_ids)
            self._batch_ids = [self._current_email_id]
            email = EMAIL_BY_ID[self._current_email_id]
            context = (
                f"Email requiring a reply:\n"
                f"  ID: {self._current_email_id}\n"
                f"  From: {email['sender_name']} <{email['sender']}>\n"
                f"  Subject: {email['subject']}\n"
                f"  (Use get_email('{self._current_email_id}') to read the full body)"
            )

        message = (
            f"{task_def['description']}\n"
            f"{'─' * 60}\n"
            f"{context}\n"
            f"{'─' * 60}\n"
            f"Max steps: {self._max_steps}  |  Episode: {self._state.episode_id[:8]}"
        )

        return Observation(
            done=False,
            reward=_clamp(0.0),
            metadata={
                "task_name": self._task_name,
                "message": message,
                "email_ids": self._batch_ids,
                "step_count": 0,
            },
        )

    def _step_impl(self, action: Any, timeout_s: Optional[float] = None, **kwargs: Any) -> Observation:
        """Handle non-MCP actions (fallback)."""
        return Observation(
            done=self._done,
            reward=_clamp(self._cumulative_score),
            metadata={"error": f"Unknown action type: {type(action).__name__}. Use MCP tool calls."},
        )

    def step(self, action: Any, timeout_s: Optional[float] = None, **kwargs: Any) -> Observation:
        """Execute a step; check max_steps termination."""
        if self._state.step_count >= self._max_steps and not self._done:
            self._done = True

        obs = super().step(action, timeout_s=timeout_s, **kwargs)

        # Attach current reward/done to every observation
        obs.reward = _clamp(self._step_rewards[-1] if self._step_rewards else 0.0)
        obs.done = self._done
        obs.metadata = obs.metadata or {}
        obs.metadata["cumulative_score"] = _clamp(self._cumulative_score)
        obs.metadata["step_count"] = self._state.step_count
        return obs

    async def step_async(self, action: Any, timeout_s: Optional[float] = None, **kwargs: Any) -> Observation:
        """Async step used by WebSocket handler."""
        obs = await super().step_async(action, timeout_s=timeout_s, **kwargs)
        obs.reward = _clamp(self._step_rewards[-1] if self._step_rewards else 0.0)
        obs.done = self._done
        obs.metadata = obs.metadata or {}
        obs.metadata["cumulative_score"] = _clamp(self._cumulative_score)
        obs.metadata["step_count"] = self._state.step_count
        return obs

    @property
    def state(self) -> State:
        """Return current episode state."""
        return self._state
