---
doc_id: helios-admin-roles
tenant_id: northwind
title: Admin roles and permissions
doc_type: guide
version: v3
effective_from: 2026-01-15
superseded_at: null
url_path: /guides/admin-roles
---

# Admin roles and permissions

> Synthetic Helios documentation for the `northwind` tenant. Version `v3`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

Helios has four built-in roles, optional custom roles and SCIM group mapping. Owners manage billing, security and the workspace. Admins manage members, projects and integrations. Members create and edit work. Viewers and Guests have read-only access with different visibility rules.

<!-- page: 2 -->

## Assign a role

<a id="assign-a-role"></a>

Open Settings > Members, choose a member and select Change role. Every workspace must keep at least one Owner. Guests are invited from a project and only see projects they are added to. With SCIM enabled, group membership can assign built-in roles automatically.

## Permissions

<a id="permissions"></a>

Custom roles start from a built-in role and add granular permissions such as project.create, member.invite, audit.export and webhook.manage. A custom role cannot grant billing.manage or workspace.delete; those stay with the Owner role. Permission changes apply at the next request.

<!-- page: 3 -->

## Audit log access

<a id="audit-log-access"></a>

Audit log export requires the Owner role or a custom role with the audit.export permission. The export covers the previous 90 days, is delivered as a CSV download, and the download link expires after 24 hours. SCIM provisioning events include the source identity provider and the mapped group.
