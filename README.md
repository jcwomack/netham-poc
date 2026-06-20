<!--
SPDX-FileCopyrightText: © 2026 James C. Womack
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# netham-early-access

[Netham Lock](https://en.wikipedia.org/wiki/Netham_Lock) is the point at which boats from the River Avon can access the Bristol Floating Harbour.

`netham` is a command line tool for acquiring temporary AWS credentials for a role assumed using the STS API via an OAuth 2.0/OpenID Connect web identity token.

The primary use case is to enable service users with identities stored in an OAuth 2.0/OpenID Connect compliant IAM service (e.g. Keycloak) to acquire access to resources via an AWS-style API (e.g. S3) by assuming a role that has access to those resources.

## Early access version

This repository contains a minimal version of `netham` written in Python. This is being developed and refined in collaboration with users during an early access period, to address pain points and improve user experience.

The goal of development during the early access period is to produce a reference implementation, which can then be used as the basis for a clean reimplementation. Python was chosen for this initial version to produce a clear and readable reference. It is anticipated that the reimplementation will be done using Rust, to produce strongly typed, memory safe code that can be distributed as a single self-contained binary.

Users of the early access version of `netham` should be aware that it will not receive ongoing maintenance or updates beyond the early access period. Once the clean reimplementation is in place, this repository will be archived and users should migrate to the reimplemented version.

## Motivating example

Access to per-user S3 buckets using a OAuth 2.0/OIDC web identity token.

### Setup

* Each user is provisioned a bucket in an S3-compatible storage provider, named with a unique per-user identifier
* The S3-compatible storage provider implements the STS API and has a role that can be assumed using the `AssumeRoleWithWebIdentity` endpoint
* The policies that grant access to per-user buckets restrict the accessible buckets on the basis of the value in claim(s) of the token (e.g. `sub`)
* Each user has an identity registered with a OAuth 2.0/OpenID Connect compliant IAM service and the provider has been registered to the S3-compatible storage as an IdP
* A client has been created in the IAM service which issues tokens to authenticated users where claim(s) contain a unique per-user identifier that maps to bucket access via IAM policy

### Execution

* `netham` is a command line tool run on a user's computer
* `netham` acts as a client in an OAuth 2.0 flow with the IAM service (authorization server) to acquire a token
* `netham` immediately exchanges the token for temporary credentials to assume the role needed to access the per-user S3 bucket
* `netham` returns to the user the AWS credentials in a form that is compatible with S3 clients (e.g. environment variables)
