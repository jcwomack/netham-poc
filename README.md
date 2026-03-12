<!--
SPDX-FileCopyrightText: © 2026 James C. Womack
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# netham-poc

[Netham Lock](https://en.wikipedia.org/wiki/Netham_Lock) is the point at which boats from the River Avon can access the Bristol Floating Harbour.

`netham` is a command line tool for acquiring temporary AWS credentials for a role assumed using the STS API via an OAuth 2.0/OpenID Connect web identity token.

The primary use case is to enable service users with identities stored in an OAuth 2.0/OpenID Connect compliant IAM service (e.g. Keycloak) to acquire access to resources by assuming a role that has provides access to those resources.

## Motivating example

### Setup

* Each user is provisioned a bucket in S3-compatible storage provider names with a unique identifier
* The S3-compatible storage provider implements the STS API and has a role that can be assumed using the AssumeRoleWithWebIdentity endpoint
* The policies that grant access to per-user buckets on the basis of the value in the `sub` claim of the token
* Each user has an identity registered with a OAuth 2.0/OpenID Connect compliant IAM service and the provider has been registered to the S3-compatible storage as an IdP 
* A client has been created in the IAM service which issues tokens to authenticated users where the `sub` claim contains the unique identifier for the per-user bucket

### Execution

* `netham` is a command line tool run on a user's computer
* `netham` acts as a client in an OAuth 2.0 flow with the IAM service (authorization server) to acquire a token
* `netham` immediately exchanges the token for temporary credentials to assume the role needed to access the per-user S3 bucket
* `netham` returns to the user the AWS credentials in a form that is compatible with S3 clients (e.g. environment variables)