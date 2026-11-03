---
doc_id: helios-integrations
tenant_id: acme
title: Integrations
doc_type: guide
version: v1
effective_from: 2024-01-15
superseded_at: 2025-01-15
url_path: /guides/integrations
---

# Integrations

> Synthetic Helios documentation for the `acme` tenant. Version `v1`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

Helios 1.0 supports Slack, GitHub and Google Calendar. Install an integration from Settings > Integrations and authorize the workspace. Each integration has its own permissions page.

## Slack and Teams

<a id="slack-and-teams"></a>

The Slack integration posts task and project updates to a channel and lets members create tasks with the /helios slash command. Link a channel to a project to keep updates in one place.

<!-- page: 2 -->

## GitHub and GitLab

<a id="github-and-gitlab"></a>

The GitHub integration links pull requests and commits to tasks when the task reference appears in the title or body. Merging a linked pull request can move the task to Done if the project enables it.

## Calendar and Jira

<a id="calendar-and-jira"></a>

The Google Calendar integration mirrors task due dates into a read-only Helios calendar. The Jira integration links Helios tasks to Jira issues and syncs status in both directions when the mapping is enabled.

<!-- page: 3 -->

## Permissions and limits

<a id="permissions-and-limits"></a>

An integration acts as the member who installed it. If that member leaves the workspace, an Owner must reconnect the integration. Each workspace can have up to 20 active integrations and 100 linked projects.

## Troubleshooting

<a id="troubleshooting"></a>

If an integration stops posting, check Settings > Integrations for an expired authorization and reconnect it. Slack rate limits can delay messages during busy periods. GitHub events are delivered once; Helios does not replay missed events.
