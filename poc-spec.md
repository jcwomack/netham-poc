<!--
SPDX-FileCopyrightText: © 2026 James C. Womack
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Specification for `netham` proof-of-concept

## Note: Transition to reference minimal viable product

This specification was created to be used as a starting point for a proof-of-concept implementation for the `netham` tool. The proof-of-concept code was successfully created and demonstrated the technical feasibility of the command line user flow for acquiring temporary AWS credentials using a web identity token.

After demonstrating feasibility it was determined that the proof-of-concept code was sufficiently capable and robust to be used as the basis for a minimal viable product (MVP). The MVP will be developed and refined in collaboration with users during an early access period, to address pain points and improve user experience.

During the early access period we will iterate on the MVP based on user feedback and bug reports, producing a reference implementation. This will then be used as the starting point for a clean reimplementation. The reimplementation will provide the opportunity to shed technical debt accrued during early development and allow the adoption of tooling/processes/constructs that promote security and robustness.

## Principles

This is a proof-of-concept that may be used as the basis for a future software package. It is intended as a demonstration of a possible user flow for accessing AWS credentials using a web identity token. If the proof-of-concept is successful, it may be used as a reference for a more robust implementation.

To enable us to assess the proof-of-concept and potentially use as a reference implementation, we should follow these principles:

* Simplicity and readability of code should be preferred over optimisation
* Make use of third party libraries and packages only where this is necessary and where it serves the simplicity and readability of the code
* Avoid use of complex programming constructs where simpler ones would be sufficient
* Document all functional elements clearly and concisely using language-appropriate methods

## Tooling choices

The following should be used

* Python programming language
  * Type annotations
  * Sphinx-style docstrings
  * Target Python 3.11 and higher
* `uv` package and project manager
  * Packaged application with `src`-layout
  * Script-type entry point for command line usage
* AWS Python SDK for communicating with AWS APIs
* Device authorization grant (RFC 8628) for acquiring an identity token from the IAM service
* Configuration stored in TOML format

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

## Prototype flow

Example prototype flow that performs the key steps using `curl` and the AWS CLI. `netham` should replicate this flow, in Python as described below.

Make device authorization request

```console
$ curl -sS "https://keycloak.example.com/realms/example/protocol/openid-connect/auth/device" \
  -d "client_id=sts-s3-client" \
  | jq -r '"\(.device_code) \(.user_code) \(.verification_uri_complete)"' \
  | read -r DEVICE_CODE USER_CODE VERIFICATION_URI_COMPLETE; \
  echo "Go to ${VERIFICATION_URI_COMPLETE} in a web browser"
Go to <verification URI> in a web browser
```

User goes to the URI in the web browser, verifies the code, and consents to accessing resources.

Device access token request (would usually be done by the client polling the token endpoint)

```console
$ curl -sS "https://keycloak.example.com/realms/example/protocol/openid-connect/token" \
  -d "grant_type=urn:ietf:params:oauth:grant-type:device_code" \
  -d "client_id=sts-s3-client" \
  -d "device_code=${DEVICE_CODE}" | jq -r '.access_token' | read -r ACCESS_TOKEN
```

Assume role with STS

```console
$ aws sts assume-role-with-web-identity \
  --role-arn arn:aws:iam::123456789101:role/KeycloakRole \
  --role-session-name test-session \
  --web-identity-token "${ACCESS_TOKEN}" \
  | jq -r '.Credentials | "\(.AccessKeyId) \(.SecretAccessKey) \(.SessionToken)"' \
  | read -r AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN \
  ; export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```

At this point the user can use standard AWS client tools to interact with resources that the assumed role can access.

## User interface

```console
$ netham auth --output creds_env.sh
Open this URL in your browser:

https://keycloak.example.com/realms/example/device?user_code=ABCD-EFGH

## User opens browser to authenticate while application polls token endpoint

S3 temporary access credentials acquired for user test_user. Add these to your environment by running 

source creds_env.sh
```

The `creds_env.sh` file is a simple script to add the access credentials to the shell environment:

```console
$ cat creds_env.sh
#!/bin/bash
export AWS_ACCESS_KEY_ID="<AWS access key ID>"
export AWS_SECRET_ACCESS_KEY="<AWS secret access key>"
export AWS_SESSION_TOKEN="<AWS session token>"
```

The user can add the credentials to their environment, then use a standard S3 client like AWS CLI to interact with staging storage buckets they have been granted access to:

```console
$ source creds_env.sh
$ aws s3 ls test_user
2026-03-03 10:57:37      12273 Nyan_cat_250px_frame.PNG
```
