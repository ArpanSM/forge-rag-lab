---
doc_id: helios-projects-and-tasks
tenant_id: acme
title: "Projects, tasks and views"
doc_type: guide
version: v3
effective_from: 2026-01-15
superseded_at: null
url_path: /guides/projects-and-tasks
---

# Projects, tasks and views

> Synthetic Helios documentation for the `acme` tenant. Version `v3`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

Projects contain tasks, subtasks, dependencies and milestones. Use milestones for delivery dates, dependencies for sequencing and workload for capacity planning. Every task has a reference, status, assignee, estimate and optional due date.

## Projects and views

<a id="projects-and-views"></a>

List, Board, Timeline and Workload views share the same task data. Timeline shows dependencies and milestones. Workload groups open task estimates by assignee and week so you can spot overallocation.

## Task fields

<a id="task-fields"></a>

Task fields include title, description, assignee, reporter, status, priority, estimate, start date, due date, labels, custom fields and attachments. Estimates use person-days and accept increments of 0.5.

<!-- page: 2 -->

## Status and workflow

<a id="status-and-workflow"></a>

The default workflow is Backlog, To do, In progress, In review, Blocked and Done. Admins can rename, reorder and add statuses, and choose which statuses count as closed. A task can move backwards if the workflow allows it.

## Comments and mentions

<a id="comments-and-mentions"></a>

Comments support @mentions, reactions, file attachments and threaded replies. Editing a comment keeps the previous version in the task activity log for 90 days. Resolving a thread hides it from the default comment view.

## Milestones and workload

<a id="milestones-and-workload"></a>

Add a milestone from the project sidebar and set a target date. Workload view counts open task estimates per assignee. A person is overallocated when assigned estimates exceed their weekly capacity, which defaults to five person-days.

<!-- page: 3 -->

## Saved views and export

<a id="saved-views-and-export"></a>

Saved views can be personal, shared with a project or published to the workspace. A view stores filters, sort order, grouping, visible columns and the selected layout. CSV exports include visible rows and columns.

## Automations

<a id="automations"></a>

Project automations can assign a task, change status or post a comment when a trigger fires. Triggers include task created, status changed and due date approaching. Automations run as the workspace owner and appear in the audit log.
