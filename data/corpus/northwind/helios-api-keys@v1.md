---
doc_id: helios-api-keys
tenant_id: northwind
title: API keys
doc_type: api
version: v1
effective_from: 2024-01-15
superseded_at: 2025-01-15
url_path: /api/keys
---

# API keys

> Synthetic Helios documentation for the `northwind` tenant. Version `v1`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

API keys authenticate server-to-server requests to the Helios API. Send the key in the Authorization header as a Bearer token. Keys are workspace credentials; never ship them in browser code or mobile apps.

## Create a key

<a id="create-a-key"></a>

Open Settings > Developer > API keys and choose Create key. The full key is shown once. Copy it before closing the dialog; Helios stores only a fingerprint and cannot show the secret again. Keys inherit the permissions of the member who created them.

<!-- page: 2 -->

## Key lifetime

<a id="key-lifetime"></a>

API keys do not expire. Helios does not provide key rotation in v1. To replace a key, create a second key, deploy it, and then revoke the first key. A workspace can have up to ten active keys.

## Rotate a key

<a id="rotate-a-key"></a>

Helios does not provide a rotation action in v1. Create a second key, deploy it, verify traffic, and then revoke the first key. A workspace can have up to ten active keys.

## Scopes

<a id="scopes"></a>

Keys have workspace-wide access in v1. There are no read-only or project-scoped keys. Create a separate key per service so that one credential can be revoked without interrupting other integrations.

<!-- page: 3 -->

## Revoke a key

<a id="revoke-a-key"></a>

Key creation and revocation appear in Settings > Audit log. Requests made with a key are attributed to the key owner in project activity.

## Common errors

<a id="common-errors"></a>

401 invalid_key means the key is unknown or malformed. 401 key_expired means the key passed its 90-day limit. 403 insufficient_scope means the key is valid but lacks the scope required by the endpoint. Include the request ID from the response when contacting support.
