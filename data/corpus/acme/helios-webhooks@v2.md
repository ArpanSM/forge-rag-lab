---
doc_id: helios-webhooks
tenant_id: acme
title: Webhooks
doc_type: api
version: v2
effective_from: 2025-01-15
superseded_at: 2026-01-15
url_path: /api/webhooks
---

# Webhooks

> Synthetic Helios documentation for the `acme` tenant. Version `v2`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

Webhooks send an HTTP POST to your endpoint when an event happens in Helios. Create an endpoint under Settings > Developer > Webhooks, choose the events and store the signing secret securely.

## Signature verification

<a id="signature-verification"></a>

Each delivery includes an X-Helios-Signature-256 header containing an HMAC-SHA256 digest of the raw request body. Compute the digest with the endpoint secret and compare it in constant time before parsing JSON. SHA-1 signatures are accepted until 2025-06-30.

<!-- page: 2 -->

## Retries and delivery

<a id="retries-and-delivery"></a>

Helios retries failed deliveries five times with exponential backoff starting at one minute and capped at one hour. A delivery is successful when the endpoint returns any 2xx status within ten seconds. Endpoints that time out are treated as failed.

## Event types

<a id="event-types"></a>

Available events include project.created, project.updated, project.deleted, task.created, task.updated, task.deleted, comment.created and member.invited. Payloads include the workspace ID, event type, timestamp and the changed object.

<!-- page: 3 -->

## Manage endpoints

<a id="manage-endpoints"></a>

Rotate a secret from the endpoint menu; the previous secret remains valid for 24 hours. Disable an endpoint to stop new deliveries without deleting its history. Delivery logs retain request headers, response status and latency for 30 days.

## Replay a delivery

<a id="replay-a-delivery"></a>

Open the endpoint delivery log, select a failed delivery and choose Replay. Replays use the current endpoint secret and count toward the retry budget. A delivery can be replayed up to ten times in 24 hours.
