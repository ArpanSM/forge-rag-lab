---
doc_id: helios-billing-plans
tenant_id: acme
title: Billing plans and invoices
doc_type: policy
version: v3
effective_from: 2026-01-15
superseded_at: null
url_path: /policies/billing-plans
---

# Billing plans and invoices

> Synthetic Helios documentation for the `acme` tenant. Version `v3`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

Helios bills per active member. Starter is free for up to five members and three projects. Team is USD 16 per member per month billed annually; Business is USD 32 per member per month billed annually. Monthly billing costs 20 percent more.

<a id="overview-2"></a>

Team includes 250 GB of storage, 100,000 API requests and standard support. Business includes 1 TB, 500,000 requests, SAML SSO, SCIM, audit export and a 99.9 percent uptime target. Enterprise terms are available through sales.

## Plans and included usage

<a id="plans-and-included-usage"></a>

The plan table lists the included quotas for each plan. Quotas reset at the start of each UTC calendar month. Unused API requests do not roll over. Storage is measured as the average daily stored bytes for the month, including attachments and exports.

<!-- page: 2 -->

## Seats and plan changes

<a id="seats-and-plan-changes"></a>

A seat is an active member or guest; Viewers consume a seat. Adding a seat mid-cycle is prorated. Removing a seat takes effect at the next renewal. Upgrading a plan is immediate and prorated; downgrading takes effect at the next renewal after the current annual commitment ends.

<a id="seats-and-plan-changes-2"></a>

Unused seat credits from a downgrade expire after 60 days. Credits cannot be transferred to another workspace or used to pay overages.

<!-- page: 3 -->

## Usage and overages

<a id="usage-and-overages"></a>

Team includes 100,000 API requests and 250 GB of storage per month. Business includes 500,000 requests and 1 TB. Additional API usage costs USD 0.20 per 1,000 requests; additional storage costs USD 0.10 per GB per month. Usage is measured in UTC calendar months.

<a id="usage-and-overages-2"></a>

A workspace is notified at 80 percent and 100 percent of each quota. Notifications go to Owners and to the billing email address. Crossing a quota does not interrupt service unless the account is more than 30 days past due.

<!-- page: 4 -->

## Invoices and payment

<a id="invoices-and-payment"></a>

Owners can download invoices from Settings > Billing. Card payments are charged automatically. Annual Business plans can request NET 30 terms during the sales process. Failed payments retry after three and seven days, then the workspace becomes read-only.

## Overage grace period

<a id="overage-grace-period"></a>

Annual Business plans include a 14-day overage grace period before overage invoices are issued. If the overage is paid within that window, no late fee applies. Monthly Business plans and all Team plans have no grace period; their overages are billed on the next monthly invoice.

<a id="overage-grace-period-2"></a>

Grace applies only to metered API and storage overages, not to additional seats. A workspace that cancels during the grace period still owes the metered usage for that month.

<!-- page: 5 -->

## Cancellation and refunds

<a id="cancellation-and-refunds"></a>

Cancelling ends the plan at the end of the current term. The workspace becomes read-only for 30 days and is then deleted. Monthly plans are not refunded. Annual plans may receive a refund for unused full months if cancelled within 14 days of purchase.

<a id="cancellation-and-refunds-2"></a>

Prices exclude taxes. Helios adds VAT, GST or sales tax when the billing address requires it. Refunds are returned to the original payment method within ten business days.
