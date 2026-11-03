---
doc_id: helios-sso-policy
tenant_id: northwind
title: Single sign-on policy
doc_type: policy
version: v2
effective_from: 2025-01-15
superseded_at: 2026-01-15
url_path: /policies/sso
---

# Single sign-on policy

> Synthetic Helios documentation for the `northwind` tenant. Version `v2`. Not real product documentation.

<!-- page: 1 -->

## Overview

<a id="overview"></a>

Single sign-on lets members authenticate through your identity provider instead of a Helios password. SSO is configured per workspace and can be enforced for every member except the break-glass Owner account.

## Session policy

<a id="session-policy"></a>

SAML 2.0 single sign-on is available on the Business plan. Helios supports service-provider-initiated and identity-provider-initiated sign-in. Just-in-time provisioning creates a Member account on first sign-in. SAML sessions expire after 12 hours in v2.

## Provisioning

<a id="provisioning"></a>

SCIM provisioning is not available in v2. Group membership does not change Helios roles automatically; an Admin must assign roles.

<!-- page: 2 -->

## Configure SAML

<a id="configure-saml"></a>

In your identity provider, create a SAML application and use the workspace metadata URL from Settings > Security > SSO. Set the ACS URL to https://app.helios.example/saml/acs and the entity ID to the workspace ID shown on the same page.

<a id="configure-saml-2"></a>

Upload the identity provider metadata XML or enter the SSO URL and signing certificate manually. Helios validates the audience, recipient and signature on every assertion. Clock skew is limited to two minutes.

## Verify domains

<a id="verify-domains"></a>

Add every email domain that should use SSO and verify it with a DNS TXT record. A domain can belong to only one workspace. Members with an unverified domain continue to sign in with their Helios password unless enforcement is on.

<!-- page: 3 -->

## Enforce SSO

<a id="enforce-sso"></a>

Owners can choose Optional or Required. Required SSO blocks password sign-in for every member whose email domain is verified, except the break-glass Owner. Keep at least two Owners with working SSO access before enabling enforcement.

## Troubleshooting

<a id="troubleshooting"></a>

A signature error usually means the certificate in Helios is stale. An audience mismatch means the entity ID in the identity provider does not match the workspace. After changing certificates, sign out and retry in a private browser window.
