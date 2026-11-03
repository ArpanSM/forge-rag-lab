---
doc_id: helios-projects-and-tasks
tenant_id: northwind
title: "Projects, tasks and views"
doc_type: guide
version: v2
effective_from: 2025-01-15
superseded_at: 2026-01-15
url_path: /guides/projects-and-tasks
---

# Projects, tasks and views

> Synthetic Helios documentation for the `northwind` tenant. Version `v2`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

Projects contain tasks, subtasks and dependencies. Use dependencies when one task must finish before another can start. Every task has a reference, status, assignee, estimate and optional due date.

## Projects and views

<a id="projects-and-views"></a>

List, Board and Timeline views share the same task data. Timeline draws dependency arrows and highlights tasks that would move a downstream due date. Board view groups tasks by status or assignee.

## Task fields

<a id="task-fields"></a>

Task fields include title, description, assignee, reporter, status, priority, estimate, start date, due date, labels and attachments. Custom fields can be added to a project by an Admin.

<!-- page: 2 -->

## Status and workflow

<a id="status-and-workflow"></a>

The default workflow is Backlog, To do, In progress, In review and Done. Admins can rename statuses, reorder them and choose which statuses count as closed. A task can move backwards if the workflow allows it.

## Comments and mentions

<a id="comments-and-mentions"></a>

Comments support @mentions, reactions and file attachments. Editing a comment adds an edited marker and keeps the previous version in the task activity log for 30 days.

## Dependencies and recurring tasks

<a id="dependencies-and-recurring-tasks"></a>

Open a task, choose Dependencies and add a blocking task. Helios warns when a due date conflicts with an upstream dependency, but it does not block the save. Recurring tasks repeat daily, weekly or monthly and create the next occurrence when the current task is marked Done.

<!-- page: 3 -->

## Saved views and export

<a id="saved-views-and-export"></a>

Saved views can be personal or shared with the project. A view stores filters, sort order, grouping and visible columns. Exports to CSV include the rows and columns currently visible.
