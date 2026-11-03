---
doc_id: helios-api-keys
tenant_id: northwind
title: API keys
doc_type: api
version: v2
effective_from: 2025-01-15
superseded_at: 2026-01-15
url_path: /api/keys
---

# API keys

> Synthetic Helios documentation for the `northwind` tenant. Version `v2`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

API keys authenticate server-to-server requests to the Helios API. Send the key in the Authorization header as a Bearer token. Keys are workspace credentials; never ship them in browser code or mobile apps.

## Create a key

<a id="create-a-key"></a>

Open Settings > Developer > API keys and choose Create key. Choose the read, write or admin scope, name the key and copy the secret from the confirmation dialog. The full key is shown once; Helios stores only a fingerprint.

<!-- page: 2 -->

## Key lifetime

<a id="key-lifetime"></a>

API keys expire 90 days after creation. The API returns HTTP 401 with the error code key_expired for an expired key. Rotate keys before day 90; in v2 the old key stops working as soon as rotation completes.

## Rotate a key

<a id="rotate-a-key"></a>

Open Settings > Developer > API keys, select a key and choose Rotate. The replacement key is shown once and keeps the same scopes. Update the service environment variable before the old key is revoked; the old key stops working when rotation completes.

## Scopes

<a id="scopes"></a>

Choose scopes when creating a key: read, write or admin. Read keys can list projects and tasks; write keys can create and update them; admin keys can also manage members and webhooks. Grant the smallest scope that the integration needs.

<!-- page: 3 -->

## Revoke a key

<a id="revoke-a-key"></a>

Key creation, rotation and revocation emit audit events with the actor, key prefix and source IP address. Request logs retain the key prefix, never the secret.

## Common errors

<a id="common-errors"></a>

401 invalid_key means the key is unknown or malformed. 401 key_expired means the key passed its 90-day limit. 403 insufficient_scope means the key is valid but lacks the scope required by the endpoint. Include the request ID from the response when contacting support.
