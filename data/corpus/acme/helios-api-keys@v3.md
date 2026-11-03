---
doc_id: helios-api-keys
tenant_id: acme
title: API keys
doc_type: api
version: v3
effective_from: 2026-01-15
superseded_at: null
url_path: /api/keys
---

# API keys

> Synthetic Helios documentation for the `acme` tenant. Version `v3`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

API keys authenticate server-to-server requests to the Helios API. Send the key in the Authorization header as a Bearer token. Keys are workspace credentials; never ship them in browser code or mobile apps.

## Create a key

<a id="create-a-key"></a>

Open Settings > Developer > API keys and choose Create key. Choose the read, write or admin scope, optionally limit the key to specific projects on a Business plan, name the key and copy the secret from the confirmation dialog. The full key is shown once.

<!-- page: 2 -->

## Key lifetime

<a id="key-lifetime"></a>

API keys expire 90 days after creation. Rotation creates a 24-hour overlap: the replacement key works immediately and the old key keeps working until the overlap ends. After 24 hours the old key returns HTTP 401 with the error code key_expired.

## Rotate a key

<a id="rotate-a-key"></a>

Open Settings > Developer > API keys, select a key and choose Rotate. Choose the overlap window (1 to 24 hours, default 24) and copy the new key. The replacement inherits the original scopes unless you edit them before confirming.

## Scopes

<a id="scopes"></a>

Choose scopes when creating a key: read, write, admin or a comma-separated combination such as read,write. Admin keys can manage members, webhooks and billing exports. Project-scoped keys are available on Business plans and restrict access to listed projects.

<!-- page: 3 -->

## Revoke a key

<a id="revoke-a-key"></a>

Key creation, rotation, scope changes and revocation emit audit events with the actor, key prefix and source IP address. The audit log retains key events for 365 days. Request logs retain the key prefix, never the secret.

## Common errors

<a id="common-errors"></a>

401 invalid_key means the key is unknown or malformed. 401 key_expired means the key passed its 90-day limit. 403 insufficient_scope means the key is valid but lacks the scope required by the endpoint. Include the request ID from the response when contacting support.
