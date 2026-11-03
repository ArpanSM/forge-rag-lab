---
doc_id: helios-admin-roles
tenant_id: northwind
title: Admin roles and permissions
doc_type: guide
version: v2
effective_from: 2025-01-15
superseded_at: 2026-01-15
url_path: /guides/admin-roles
---

# Admin roles and permissions

> Synthetic Helios documentation for the `northwind` tenant. Version `v2`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

Helios has four built-in roles and optional custom roles. Owners manage billing, security and the workspace. Admins manage members, projects and integrations. Members create and edit work. Viewers and Guests have read-only access with different visibility rules.

<!-- page: 2 -->

## Assign a role

<a id="assign-a-role"></a>

Open Settings > Members, choose a member and select Change role. Every workspace must keep at least one Owner. Guests are invited from a project rather than the workspace directory and only see projects they are added to.

## Permissions

<a id="permissions"></a>

Custom roles start from a built-in role and add granular permissions such as project.create, member.invite and audit.export. A custom role cannot grant billing.manage or workspace.delete; those stay with the Owner role. Permission changes apply at the next request.

<!-- page: 3 -->

## Audit log access

<a id="audit-log-access"></a>

Audit log export requires the Owner role or a custom role with the audit.export permission. The export covers the previous 30 days, is delivered as a CSV download, and the download link expires after seven days. Invitations, role changes, project deletions and SSO changes are always recorded.
