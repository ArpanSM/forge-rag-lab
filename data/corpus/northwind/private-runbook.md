---
doc_id: private-runbook
tenant_id: northwind
title: Northwind incident escalation runbook
doc_type: guide
version: v3
effective_from: 2026-03-01
superseded_at: null
url_path: /private/incident-runbook
---

# Northwind incident escalation runbook

> Synthetic Helios documentation for the `northwind` tenant. Version `v3`. Not real product documentation.

<!-- page: 1 -->

## Confidentiality

<a id="confidentiality"></a>

Confidential — Northwind only. This runbook is not part of the shared Helios documentation and must not be returned to another tenant. northwind-private marker: NW-RUNBOOK-7.

## Severity levels

<a id="severity-levels"></a>

SEV-1 is a full workspace outage or confirmed data exposure; page the on-call lead immediately. SEV-2 is a major feature unavailable for more than 30 minutes. SEV-3 is degraded performance with a workaround. Record every incident in the Northwind operations channel.

<!-- page: 2 -->

## Escalation path

<a id="escalation-path"></a>

Start with the Northwind platform on-call, then the workspace owner, then the Helios support escalation contact. The owner is the only person who can approve a production data restore. During a SEV-1, update the incident channel every 15 minutes until mitigation.

## Maintenance window

<a id="maintenance-window"></a>

Northwind reserves Sunday 02:00–04:00 UTC for changes. No production deploys during quarter-end close or the first two business days of each month. Emergency changes require approval from the workspace owner and the security lead.
