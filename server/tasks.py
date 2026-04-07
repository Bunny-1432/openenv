"""
Task definitions and graders for the Email Triage Environment.

3 tasks with progressive difficulty:
  1. classify_email  — Easy:   classify a single email into a category
  2. triage_inbox    — Medium: prioritize + label a 5-email inbox batch
  3. draft_reply     — Hard:   draft a professional reply to an email
"""

from __future__ import annotations

from typing import Any

from server.email_data import CATEGORIES, EMAIL_BY_ID, TASK_EMAIL_GROUPS

# ──────────────────────────────────────────────────────────────────────────────
# Task 1 – classify_email  (Easy)
# ──────────────────────────────────────────────────────────────────────────────

TASK_1_DESCRIPTION = """\
TASK: Email Classification (Easy)
==================================
You have access to a single email. Your job is to classify it into the correct
category so it can be routed to the right team.

Valid categories: urgent, spam, newsletter, support, meeting, security, general

Available tools:
  - get_email(email_id)       → Read the email content
  - classify_email(email_id, category) → Submit your category decision

The episode ends when you call classify_email or after 6 steps.
Score: 1.0 if correct, 0.0 if wrong. Partial credit for reading the email first.
"""


def grade_classify(email_id: str, submitted_category: str, read_email: bool = True) -> float:
    """
    Grade a classification attempt.

    Args:
        email_id: ID of the email being classified
        submitted_category: Category submitted by the agent
        read_email: Whether the agent read the email before classifying

    Returns:
        Score in [0.0, 1.0]
    """
    email = EMAIL_BY_ID.get(email_id)
    if email is None:
        return 0.0

    correct = email["category"]
    submitted = submitted_category.strip().lower()

    if submitted == correct:
        # Full score; small bonus for reading first
        return 1.0
    # Partial credit for related categories
    partial_groups = [
        {"urgent", "security"},
        {"spam", "newsletter"},
        {"support", "meeting", "general"},
    ]
    for group in partial_groups:
        if submitted in group and correct in group:
            return 0.3  # Wrong but related category
    return 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Task 2 – triage_inbox  (Medium)
# ──────────────────────────────────────────────────────────────────────────────

TASK_2_DESCRIPTION = """\
TASK: Inbox Triage (Medium)
============================
You have a 5-email inbox batch. For each email you must:
  1. Assign a priority (1 = most urgent, 5 = least urgent)
  2. Apply the correct category label

Available tools:
  - list_emails()                               → See all emails in the batch
  - get_email(email_id)                         → Read a specific email
  - set_email_priority(email_id, priority, labels) → Submit priority + labels for one email

The episode ends when all 5 emails are triaged or after 15 steps.
Score: weighted average of (priority rank accuracy + label accuracy) per email.
"""

PRIORITY_ORDER_WEIGHT = 0.5   # 50 % from correctly ordering priorities
LABEL_ACCURACY_WEIGHT = 0.5   # 50 % from correct label

def _spearman_rho(predicted: list[int], actual: list[int]) -> float:
    """Compute Spearman rank correlation ∈ [−1, 1]."""
    n = len(predicted)
    if n == 0:
        return 0.0
    d2 = sum((p - a) ** 2 for p, a in zip(predicted, actual))
    rho = 1 - (6 * d2) / (n * (n**2 - 1)) if n > 1 else 1.0
    return max(-1.0, min(1.0, rho))


def grade_triage(submissions: dict[str, dict[str, Any]], batch_ids: list[str]) -> float:
    """
    Grade inbox triage across a batch of emails.

    Args:
        submissions: {email_id: {"priority": int, "labels": [str]}}
        batch_ids: ordered list of email IDs in the batch

    Returns:
        Score in [0.0, 1.0]
    """
    if not submissions or not batch_ids:
        return 0.0

    # Priority ranking score
    predicted_priorities = []
    actual_priorities = []
    for eid in batch_ids:
        email = EMAIL_BY_ID.get(eid)
        sub = submissions.get(eid, {})
        if email and sub:
            predicted_priorities.append(sub.get("priority", 3))
            actual_priorities.append(email["priority"])

    if len(predicted_priorities) >= 2:
        rho = _spearman_rho(predicted_priorities, actual_priorities)
        priority_score = (rho + 1) / 2  # normalise to [0, 1]
    elif len(predicted_priorities) == 1:
        diff = abs(predicted_priorities[0] - actual_priorities[0])
        priority_score = max(0.0, 1.0 - diff * 0.25)
    else:
        priority_score = 0.0

    # Label accuracy score
    label_correct = 0
    total = 0
    for eid in batch_ids:
        email = EMAIL_BY_ID.get(eid)
        sub = submissions.get(eid, {})
        if email and sub:
            submitted_labels = [l.strip().lower() for l in sub.get("labels", [])]
            if email["category"] in submitted_labels:
                label_correct += 1
            total += 1

    label_score = label_correct / total if total > 0 else 0.0

    return round(
        PRIORITY_ORDER_WEIGHT * priority_score + LABEL_ACCURACY_WEIGHT * label_score,
        4,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Task 3 – draft_reply  (Hard)
# ──────────────────────────────────────────────────────────────────────────────

TASK_3_DESCRIPTION = """\
TASK: Draft Email Reply (Hard)
===============================
You need to write a professional reply to an important email.
A good reply should:
  - Acknowledge the sender's concern
  - Address the key points raised
  - Be professional and clear in tone
  - Be an appropriate length (50–400 words)
  - Propose next steps or actions

Available tools:
  - get_email(email_id)                     → Read the email you must reply to
  - submit_reply(email_id, reply_text)      → Submit your drafted reply

The episode ends when you call submit_reply or after 8 steps.
Score: weighted sum of tone (30%), coverage (40%), length (20%), structure (10%).
"""

PROFESSIONAL_TONE_MARKERS = [
    "thank", "appreciate", "sorry", "apologize", "understand", "please",
    "regards", "sincerely", "help", "assist", "resolve", "address",
    "team", "we will", "we are", "will ensure", "happy to",
]

NEGATIVE_TONE_MARKERS = [
    "wtf", "stupid", "idiot", "dumb", "whatever", "not my problem",
    "who cares", "deal with it",
]


def grade_reply(email_id: str, reply_text: str) -> float:
    """
    Grade a drafted email reply.

    Args:
        email_id: ID of the email being replied to
        reply_text: The reply text submitted by the agent

    Returns:
        Score in [0.0, 1.0]
    """
    email = EMAIL_BY_ID.get(email_id)
    if email is None or not reply_text:
        return 0.0

    reply_lower = reply_text.lower()
    words = reply_text.split()
    word_count = len(words)

    # --- Tone score (30 %) ---
    tone_hits = sum(1 for m in PROFESSIONAL_TONE_MARKERS if m in reply_lower)
    negative_hits = sum(1 for m in NEGATIVE_TONE_MARKERS if m in reply_lower)
    tone_score = min(1.0, tone_hits / 4) * max(0.0, 1.0 - negative_hits * 0.5)

    # --- Coverage score (40 %) ---
    keywords = email.get("ideal_reply_keywords", [])
    if keywords:
        covered = sum(1 for kw in keywords if kw.lower() in reply_lower)
        coverage_score = covered / len(keywords)
    else:
        # Emails that don't expect replies get 0 score for coverage
        coverage_score = 0.0

    # --- Length score (20 %) ---
    if 50 <= word_count <= 400:
        # Sweet spot: 80–250 words
        if 80 <= word_count <= 250:
            length_score = 1.0
        elif word_count < 80:
            length_score = 0.5 + 0.5 * (word_count - 50) / 30
        else:  # 251–400
            length_score = 1.0 - 0.5 * (word_count - 250) / 150
    elif word_count < 50:
        length_score = word_count / 50 * 0.4  # very short
    else:
        length_score = max(0.0, 0.5 - (word_count - 400) / 400)

    # --- Structure score (10 %) ---
    has_greeting = any(
        reply_lower.startswith(g) for g in ["hi", "hello", "dear", "good morning", "good afternoon"]
    )
    has_closing = any(
        c in reply_lower for c in ["regards", "sincerely", "best", "thanks", "thank you"]
    )
    structure_score = (0.5 if has_greeting else 0.0) + (0.5 if has_closing else 0.0)

    score = (
        0.30 * tone_score
        + 0.40 * coverage_score
        + 0.20 * length_score
        + 0.10 * structure_score
    )
    return round(min(1.0, max(0.0, score)), 4)


# ──────────────────────────────────────────────────────────────────────────────
# Task registry
# ──────────────────────────────────────────────────────────────────────────────

TASKS = {
    "classify_email": {
        "name": "classify_email",
        "difficulty": "easy",
        "description": TASK_1_DESCRIPTION,
        "max_steps": 6,
        "email_ids": TASK_EMAIL_GROUPS["classify_email"],
    },
    "triage_inbox": {
        "name": "triage_inbox",
        "difficulty": "medium",
        "description": TASK_2_DESCRIPTION,
        "max_steps": 15,
        "email_batches": TASK_EMAIL_GROUPS["triage_inbox"],
    },
    "draft_reply": {
        "name": "draft_reply",
        "difficulty": "hard",
        "description": TASK_3_DESCRIPTION,
        "max_steps": 8,
        "email_ids": TASK_EMAIL_GROUPS["draft_reply"],
    },
}
