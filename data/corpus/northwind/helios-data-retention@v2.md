---
doc_id: helios-data-retention
tenant_id: northwind
title: Data retention policy
doc_type: policy
version: v2
effective_from: 2025-01-15
superseded_at: 2026-01-15
url_path: /policies/data-retention
---

# Data retention policy

> Synthetic Helios documentation for the `northwind` tenant. Version `v2`. Not real product documentation.

<!-- page: 1 -->

## Scope

<a id="scope"></a>

This policy covers hosted Helios workspaces. It does not cover data that a customer exports and stores outside Helios. Retention periods are measured from the deletion event in UTC.

## Retention schedule

<a id="retention-schedule"></a>

Deleted projects enter a recoverable state for 30 days and are then purged within seven days. Deleted tasks are purged with their project. Audit logs are retained for 180 days. API request logs are retained for 30 days.

<a id="retention-schedule-2"></a>

Backups are encrypted at rest and retained for 35 days. A backup may contain data that was deleted after the backup was taken; restores are performed only for workspace-level recovery.

<!-- page: 2 -->

## Export before deletion

<a id="export-before-deletion"></a>

An Owner can export a project before the recoverable period ends. Exports include tasks, comments, attachments and custom fields. The download link expires after 24 hours and is not included in backups.

## Legal hold

<a id="legal-hold"></a>

A legal hold suspends deletion for named projects or members until an Owner removes the hold. Legal hold is available on Business plans. Helios notifies the workspace owner before a held project is purged.
