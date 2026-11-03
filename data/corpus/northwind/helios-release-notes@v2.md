---
doc_id: helios-release-notes
tenant_id: northwind
title: Helios release notes
doc_type: release
version: v2
effective_from: 2025-01-15
superseded_at: 2026-01-15
url_path: /releases
---

# Helios release notes

> Synthetic Helios documentation for the `northwind` tenant. Version `v2`. Not real product documentation.

<!-- page: 1 -->

## Helios 2.0

<a id="helios-2-0"></a>

Helios 2.0 was released on 2025-01-15. This release added task dependencies, recurring tasks, guest access, board view and scoped API keys. It also introduced the 2.0 API namespace.

## Highlights

<a id="highlights"></a>

Dependencies with timeline warnings. Recurring tasks for daily, weekly and monthly work. Guests who only see the projects they are added to. API keys with read, write and admin scopes.

<!-- page: 2 -->

## Improvements

<a id="improvements"></a>

Project templates copy sections, checklists and custom fields. Saved views can be shared with a project. Audit events now include the source IP address for key changes.

<!-- page: 3 -->

## Breaking changes

<a id="breaking-changes"></a>

API keys created before 2025-01-15 had no scopes and now behave as admin keys. The legacy Slack command /helios has been replaced by the Slack app. Webhook signatures use SHA-256; SHA-1 signatures are still accepted until 2025-06-30.

## Known issues

<a id="known-issues"></a>

The CSV importer does not preserve dependency links. Workload view is not available in 2.0. A recurring task may create two occurrences if the browser retries a failed completion request.
