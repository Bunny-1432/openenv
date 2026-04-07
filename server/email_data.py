"""
Synthetic email dataset for the Email Triage Environment.

All emails are deterministically generated with fixed seeds for reproducibility.
"""

import random
from typing import Any

# Fixed seed ensures reproducibility
_RNG = random.Random(42)

CATEGORIES = ["urgent", "spam", "newsletter", "support", "meeting", "security", "general"]

EMAILS: list[dict[str, Any]] = [
    # ── URGENT ──────────────────────────────────────────────────────────────
    {
        "id": "e001",
        "subject": "CRITICAL: Production database is down",
        "sender": "ops-alerts@company.com",
        "sender_name": "Ops Alerts",
        "timestamp": "2024-03-15T09:02:00Z",
        "body": (
            "ALERT: The primary production database cluster has stopped responding "
            "as of 09:00 UTC. All API endpoints returning 503. Customer impact is HIGH. "
            "On-call engineer John Smith has been paged but no response yet. "
            "Please escalate immediately. Revenue impact ~$50k/hour."
        ),
        "category": "urgent",
        "priority": 1,
        "ideal_reply_keywords": ["acknowledge", "escalate", "investigate", "status", "team"],
    },
    {
        "id": "e002",
        "subject": "Server memory critical - 97% usage",
        "sender": "monitoring@infra.company.com",
        "sender_name": "Infrastructure Monitor",
        "timestamp": "2024-03-15T10:15:00Z",
        "body": (
            "Memory usage on prod-server-07 has reached 97%. "
            "This may cause OOM crashes within the next 30 minutes. "
            "Immediate action required. Please restart the analytics worker or "
            "provision additional capacity."
        ),
        "category": "urgent",
        "priority": 1,
        "ideal_reply_keywords": ["restart", "capacity", "monitoring", "resolved", "team"],
    },
    {
        "id": "e003",
        "subject": "Urgent: Client contract renewal deadline today",
        "sender": "alice.johnson@sales.company.com",
        "sender_name": "Alice Johnson",
        "timestamp": "2024-03-15T08:30:00Z",
        "body": (
            "Hi, the Acme Corp contract expires today at 5 PM EST. "
            "I need approval on the revised pricing (attached) by 2 PM at the latest "
            "to have time to get their signature. This is a $2M annual contract. "
            "Please review and approve ASAP."
        ),
        "category": "urgent",
        "priority": 1,
        "ideal_reply_keywords": ["approve", "review", "pricing", "contract", "confirm"],
    },
    # ── SPAM ─────────────────────────────────────────────────────────────────
    {
        "id": "e004",
        "subject": "You've won $1,000,000 — claim now!",
        "sender": "noreply@lucky-winner-2024.xyz",
        "sender_name": "Prize Committee",
        "timestamp": "2024-03-15T07:00:00Z",
        "body": (
            "Congratulations! You have been selected as the lucky winner of our "
            "international lottery. Click the link below to claim your $1,000,000 prize. "
            "Act now — offer expires in 24 hours! Click: http://claim-prize.xyz/win"
        ),
        "category": "spam",
        "priority": 5,
        "ideal_reply_keywords": [],
    },
    {
        "id": "e005",
        "subject": "Make $$$ working from home — 100% guaranteed",
        "sender": "deals@quickmoney-offers.net",
        "sender_name": "Work From Home Deals",
        "timestamp": "2024-03-15T06:45:00Z",
        "body": (
            "Are you tired of your 9-to-5? Earn $5000 per week guaranteed! "
            "No experience needed. Limited spots available. "
            "Join now: http://quickmoney-offers.net/join?ref=email"
        ),
        "category": "spam",
        "priority": 5,
        "ideal_reply_keywords": [],
    },
    {
        "id": "e006",
        "subject": "FREE Viagra — no prescription needed",
        "sender": "pharmacy@discount-meds.xyz",
        "sender_name": "Discount Pharmacy",
        "timestamp": "2024-03-15T05:30:00Z",
        "body": (
            "Get cheap medications shipped directly to your door. "
            "No doctor visit required. 100% discreet packaging. "
            "Visit our online store today."
        ),
        "category": "spam",
        "priority": 5,
        "ideal_reply_keywords": [],
    },
    # ── NEWSLETTER ───────────────────────────────────────────────────────────
    {
        "id": "e007",
        "subject": "The Weekly Tech Digest — AI roundup",
        "sender": "digest@technewsletter.io",
        "sender_name": "Tech Newsletter",
        "timestamp": "2024-03-15T08:00:00Z",
        "body": (
            "This week in tech: OpenAI releases GPT-5, Google announces Gemini 2.0, "
            "and Microsoft integrates Copilot across all Office apps. "
            "Also: the latest in quantum computing breakthroughs. "
            "Unsubscribe | Manage preferences"
        ),
        "category": "newsletter",
        "priority": 4,
        "ideal_reply_keywords": [],
    },
    {
        "id": "e008",
        "subject": "DataSci Weekly: pandas 3.0 release notes",
        "sender": "hello@datasciweekly.com",
        "sender_name": "DataSci Weekly",
        "timestamp": "2024-03-15T09:00:00Z",
        "body": (
            "Hi subscriber, pandas 3.0 is out with major breaking changes. "
            "This week we cover the new copy-on-write semantics, "
            "the removal of deprecated APIs, and performance benchmarks. "
            "Read the full article on our site."
        ),
        "category": "newsletter",
        "priority": 4,
        "ideal_reply_keywords": [],
    },
    # ── SUPPORT ──────────────────────────────────────────────────────────────
    {
        "id": "e009",
        "subject": "Cannot log into my account",
        "sender": "bob.smith@customer.com",
        "sender_name": "Bob Smith",
        "timestamp": "2024-03-15T10:00:00Z",
        "body": (
            "Hi Support Team, I've been trying to log into my account for the past hour "
            "but keep getting 'Invalid credentials' even though I just changed my password. "
            "My username is bob.smith@customer.com. "
            "Please help — I have an important presentation to access from my files."
        ),
        "category": "support",
        "priority": 2,
        "ideal_reply_keywords": ["password", "reset", "account", "help", "sorry", "investigate"],
    },
    {
        "id": "e010",
        "subject": "API rate limit documentation is outdated",
        "sender": "dev@partnercompany.com",
        "sender_name": "Partner Dev Team",
        "timestamp": "2024-03-15T11:00:00Z",
        "body": (
            "Hello, your API documentation says the rate limit is 1000 req/min "
            "but we're seeing 429 errors at 500 req/min. "
            "This is causing failures in our integration. "
            "Could you please clarify the actual limits and update the docs?"
        ),
        "category": "support",
        "priority": 2,
        "ideal_reply_keywords": ["limit", "documentation", "update", "apologize", "clarify"],
    },
    # ── MEETING ──────────────────────────────────────────────────────────────
    {
        "id": "e011",
        "subject": "Q2 Planning meeting — March 20 at 2 PM",
        "sender": "sarah.chen@company.com",
        "sender_name": "Sarah Chen",
        "timestamp": "2024-03-15T09:30:00Z",
        "body": (
            "Hi team, I'd like to schedule our Q2 planning session. "
            "Proposed time: March 20 at 2 PM EST (1-hour meeting). "
            "Agenda: review Q1 results, set Q2 OKRs, resource planning. "
            "Please RSVP by end of day Thursday. Zoom link to follow."
        ),
        "category": "meeting",
        "priority": 3,
        "ideal_reply_keywords": ["confirm", "attend", "agenda", "available", "thursday"],
    },
    {
        "id": "e012",
        "subject": "Can we reschedule Tuesday's sync?",
        "sender": "mike.torres@partner.com",
        "sender_name": "Mike Torres",
        "timestamp": "2024-03-15T11:30:00Z",
        "body": (
            "Hey, something came up and I can't make Tuesday 3PM anymore. "
            "Could we move it to Wednesday afternoon or Thursday morning? "
            "Let me know what works for you."
        ),
        "category": "meeting",
        "priority": 3,
        "ideal_reply_keywords": ["reschedule", "wednesday", "thursday", "works", "alternative"],
    },
    # ── SECURITY ─────────────────────────────────────────────────────────────
    {
        "id": "e013",
        "subject": "Suspicious login attempt on your account",
        "sender": "security@company.com",
        "sender_name": "Security Team",
        "timestamp": "2024-03-15T10:45:00Z",
        "body": (
            "We detected a login attempt to your account from an unrecognized device. "
            "Location: Kyiv, Ukraine. IP: 185.220.101.XXX. Time: 10:42 UTC. "
            "If this was not you, please change your password immediately and "
            "enable 2FA. If this was you, you can safely ignore this message."
        ),
        "category": "security",
        "priority": 2,
        "ideal_reply_keywords": ["password", "2FA", "not me", "secure", "investigate"],
    },
    {
        "id": "e014",
        "subject": "CVE-2024-12345: Critical vulnerability in our dependency",
        "sender": "security-advisories@github.com",
        "sender_name": "GitHub Security",
        "timestamp": "2024-03-15T08:45:00Z",
        "body": (
            "A critical remote code execution vulnerability (CVSS 9.8) has been "
            "discovered in 'requests' library version < 2.31.0 which your project "
            "my-api uses. Please update immediately. "
            "Affected: requests==2.28.0. Fix: upgrade to requests>=2.31.0."
        ),
        "category": "security",
        "priority": 2,
        "ideal_reply_keywords": ["update", "dependency", "patch", "vulnerability", "team"],
    },
    # ── GENERAL ──────────────────────────────────────────────────────────────
    {
        "id": "e015",
        "subject": "Office kitchen cleanup reminder",
        "sender": "facilities@company.com",
        "sender_name": "Facilities",
        "timestamp": "2024-03-15T09:00:00Z",
        "body": (
            "Friendly reminder: Please clean up after yourself in the kitchen. "
            "All food should be labeled with your name and date. "
            "Unlabeled items will be removed on Fridays. Thank you!"
        ),
        "category": "general",
        "priority": 5,
        "ideal_reply_keywords": [],
    },
    {
        "id": "e016",
        "subject": "Company picnic — save the date!",
        "sender": "hr@company.com",
        "sender_name": "HR Team",
        "timestamp": "2024-03-15T10:00:00Z",
        "body": (
            "We're thrilled to announce our annual company picnic on April 15! "
            "Location: Riverside Park. Time: 12 PM – 5 PM. "
            "Bring your family! Food and activities provided. "
            "RSVP link will be shared next week."
        ),
        "category": "general",
        "priority": 5,
        "ideal_reply_keywords": [],
    },
    {
        "id": "e017",
        "subject": "Feedback on last week's product demo",
        "sender": "client.vp@bigcorp.com",
        "sender_name": "Jennifer Walsh",
        "timestamp": "2024-03-15T11:00:00Z",
        "body": (
            "Hi, I wanted to share some thoughts on the product demo your team gave last Thursday. "
            "Overall very impressive — the new dashboard is intuitive and the performance "
            "improvements are remarkable. Two suggestions: (1) the mobile experience needs work, "
            "(2) we'd love an offline mode. Look forward to the next iteration!"
        ),
        "category": "general",
        "priority": 3,
        "ideal_reply_keywords": ["thank", "feedback", "mobile", "offline", "roadmap"],
    },
    {
        "id": "e018",
        "subject": "Invoice #INV-2024-0892 — payment due March 30",
        "sender": "billing@vendor.com",
        "sender_name": "Vendor Billing",
        "timestamp": "2024-03-15T08:00:00Z",
        "body": (
            "Please find attached invoice #INV-2024-0892 for $12,450 for "
            "professional services rendered in February 2024. "
            "Payment is due March 30, 2024. "
            "Please contact billing@vendor.com with any questions."
        ),
        "category": "general",
        "priority": 3,
        "ideal_reply_keywords": ["received", "payment", "process", "accounts", "invoice"],
    },
    {
        "id": "e019",
        "subject": "New hire orientation — please complete by EOW",
        "sender": "hr@company.com",
        "sender_name": "HR Team",
        "timestamp": "2024-03-15T09:15:00Z",
        "body": (
            "Welcome to the team! Please complete the following before Friday: "
            "1. Benefits enrollment (HR portal) "
            "2. Security training (LMS) "
            "3. IT setup form (IT portal) "
            "Let your manager know if you need help with any of these."
        ),
        "category": "general",
        "priority": 3,
        "ideal_reply_keywords": ["complete", "benefits", "training", "setup", "friday"],
    },
    {
        "id": "e020",
        "subject": "Team lunch next Wednesday — restaurant vote",
        "sender": "dan.lee@company.com",
        "sender_name": "Dan Lee",
        "timestamp": "2024-03-15T12:00:00Z",
        "body": (
            "Hey team! Planning a team lunch for next Wednesday (March 20). "
            "Please vote on the restaurant: "
            "A) Sakura Sushi, B) Pita Palace, C) Cloud Nine Burgers. "
            "Reply with your choice by tomorrow!"
        ),
        "category": "general",
        "priority": 5,
        "ideal_reply_keywords": [],
    },
]

# Index by ID for fast lookup
EMAIL_BY_ID: dict[str, dict] = {e["id"]: e for e in EMAILS}

# Task-specific email groups
TASK_EMAIL_GROUPS = {
    "classify_email": [
        # One email per category to test classification
        "e001",  # urgent
        "e004",  # spam
        "e007",  # newsletter
        "e009",  # support
        "e011",  # meeting
        "e013",  # security
        "e015",  # general
    ],
    "triage_inbox": [
        # Mixed 5-email inbox batch — used in triage task
        ["e001", "e004", "e009", "e011", "e013"],  # batch 1
        ["e002", "e007", "e010", "e012", "e014"],  # batch 2
        ["e003", "e005", "e008", "e017", "e020"],  # batch 3
    ],
    "draft_reply": [
        # Urgent / support / general that benefit from replies
        "e001",
        "e009",
        "e003",
        "e010",
        "e013",
    ],
}
