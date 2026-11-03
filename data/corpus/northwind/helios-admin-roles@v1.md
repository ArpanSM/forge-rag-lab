---
doc_id: helios-admin-roles
tenant_id: northwind
title: Admin roles and permissions
doc_type: guide
version: v1
effective_from: 2024-01-15
superseded_at: 2025-01-15
url_path: /guides/admin-roles
---

# Admin roles and permissions

> Synthetic Helios documentation for the `northwind` tenant. Version `v1`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

Helios has four built-in roles. Owners manage billing, security and the workspace. Admins manage members, projects and integrations. Members create and edit work. Viewers can read projects but cannot change tasks or settings.

<!-- page: 2 -->

## Assign a role

<a id="assign-a-role"></a>

Open Settings > Members, choose a member and select Change role. Every workspace must keep at least one Owner. A member can hold only one built-in role at a time; custom roles are not available in v1.

## Permissions

<a id="permissions"></a>

Only Owners can change the billing plan, delete the workspace or enable SAML. Admins can invite members, create projects and manage webhooks. Members cannot change workspace settings. Viewers cannot comment on tasks or upload attachments.

<!-- page: 3 -->

## Audit log access

<a id="audit-log-access"></a>

The audit log records member invitations, role changes and project deletions. Owners can view the log under Settings > Audit log. Export is not available in v1.
