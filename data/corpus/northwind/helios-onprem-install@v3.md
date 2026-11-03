---
doc_id: helios-onprem-install
tenant_id: northwind
title: On-premises installation
doc_type: guide
version: v3
effective_from: 2026-02-01
superseded_at: null
url_path: /guides/on-premises
---

# On-premises installation

> Synthetic Helios documentation for the `northwind` tenant. Version `v3`. Not real product documentation.

<!-- page: 1 -->

## On-premises installation retired

<a id="on-premises-installation-retired"></a>

Helios ended sales of the on-premises distribution on 2024-12-31. The final supported on-premises release was 1.8. Helios 2.0 and later are cloud-only, and no installer, license key, activation code or upgrade package is available.

<a id="on-premises-installation-retired-2"></a>

This page is retained so that old bookmarks and support articles do not return a 404. It does not describe a supported installation procedure for Helios 2.0 or 3.0.

## Why the distribution was retired

<a id="why-the-distribution-was-retired"></a>

Operating a self-hosted deployment required customers to manage PostgreSQL, object storage, search indexes and quarterly security patches. The hosted service now provides the same data residency controls in the US and EU regions.

<!-- page: 2 -->

## Migration to the hosted service

<a id="migration-to-the-hosted-service"></a>

An owner of a 1.x deployment can request a migration assessment from Helios Support. The assessment covers data export, identity provider mapping and a cutover window. Migrations are scheduled by support; there is no self-service migration command.

<a id="migration-to-the-hosted-service-2"></a>

Export the PostgreSQL database and attachment bucket before the assessment. Do not send production credentials by email. Support provides a secure upload link after the request is approved.

## Support boundaries

<a id="support-boundaries"></a>

Support cannot issue installation media, patch an existing 1.x server or provide commands from the retired installer. Security advisories for 1.8 are no longer published. Customers still running 1.x should plan a migration or isolate the server from the public internet.
