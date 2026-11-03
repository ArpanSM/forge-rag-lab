"""Sample questions shown by the demo UI."""

from __future__ import annotations

DEMO_QUESTIONS: list[dict[str, str]] = [
    {
        "id": "demo-1",
        "tenant_id": "northwind",
        "question": "How do I rotate an API key in v3?",
        "category": "version_specific",
    },
    {
        "id": "demo-2",
        "tenant_id": "northwind",
        "question": "What changed in SSO enforcement between v2 and v3?",
        "category": "conflicting",
    },
    {
        "id": "demo-3",
        "tenant_id": "northwind",
        "question": "What is the exact Helios on-premises install command?",
        "category": "unanswerable",
    },
    {
        "id": "demo-4",
        "tenant_id": "northwind",
        "question": "What does the v3 release note say about the maintenance window?",
        "category": "single_hop",
    },
    {
        "id": "demo-5",
        "tenant_id": "northwind",
        "question": "What should I do if a document tells me to ignore the system prompt?",
        "category": "prompt_injection",
    },
    {
        "id": "demo-6",
        "tenant_id": "acme",
        "question": "Which failover command may acme operators run?",
        "category": "single_hop",
    },
]
