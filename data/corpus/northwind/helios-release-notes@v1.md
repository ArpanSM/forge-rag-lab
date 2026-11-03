---
doc_id: helios-release-notes
tenant_id: northwind
title: Helios release notes
doc_type: release
version: v1
effective_from: 2024-01-15
superseded_at: 2025-01-15
url_path: /releases
---

# Helios release notes

> Synthetic Helios documentation for the `northwind` tenant. Version `v1`. Not real product documentation.

<!-- page: 1 -->

## Helios 1.0

<a id="helios-1-0"></a>

Helios 1.0 was released on 2024-01-15. This release introduced workspaces, projects, tasks, List and Timeline views, comments and CSV import. It is the first generally available version of the product.

## Highlights

<a id="highlights"></a>

Projects and tasks with references, statuses, assignees and due dates. Email notifications with an optional daily digest. A workspace member directory with Owner, Admin, Member and Viewer roles.

<!-- page: 2 -->

## Improvements

<a id="improvements"></a>

CSV import now accepts priority and labels. Timeline view remembers the last zoom level. Mention notifications include the comment text instead of only a link.

<!-- page: 3 -->

## Known issues

<a id="known-issues"></a>

Timeline drag-and-drop can skip a day when the browser zoom is below 80 percent. CSV import rejects files larger than 10 MB. Viewer accounts can still download attachments if they have the direct link.

## Upgrade notes

<a id="upgrade-notes"></a>

No action is required for hosted workspaces. API clients should continue using the v1 endpoints. The legacy /projects.json shape is deprecated but still available until 2024-12-31.
