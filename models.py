"""
Data models for the Email Triage Environment.

The Email Triage environment simulates a real-world inbox management task
where an agent must classify, prioritize, and respond to emails.
"""

from typing import Any, Optional
from pydantic import Field

from openenv.core.env_server.types import Action, Observation


class EmailTriageAction(Action):
    """Generic action for the Email Triage environment."""

    action_type: str = Field(..., description="Type of action: classify, prioritize, reply, read, list, status")
    email_id: Optional[str] = Field(None, description="ID of the email to act on")
    category: Optional[str] = Field(
        None,
        description="Email category: spam, urgent, newsletter, support, meeting, security, general",
    )
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority 1 (highest) to 5 (lowest)")
    labels: Optional[list[str]] = Field(None, description="List of labels to apply to the email")
    reply_text: Optional[str] = Field(None, description="Reply text to send")


class EmailTriageObservation(Observation):
    """Observation from the Email Triage environment."""

    current_email: Optional[dict[str, Any]] = Field(None, description="Current email content")
    inbox_summary: Optional[list[dict[str, Any]]] = Field(None, description="Summary of inbox emails")
    feedback: str = Field(default="", description="Feedback message from the last action")
    task_name: str = Field(default="", description="Current task name")
    task_description: str = Field(default="", description="Description of the current task")
    step_reward: float = Field(default=0.0, ge=0.0, le=1.0, description="Reward from this step")
    cumulative_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Cumulative score for the episode")
    available_actions: list[str] = Field(default_factory=list, description="Available action types")
