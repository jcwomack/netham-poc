<!--
SPDX-FileCopyrightText: © 2026 James C. Womack
SPDX-License-Identifier: CC-BY-SA-4.0
-->

# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Purpose

This repository contains a minimal viable product (MVP) implementation of `netham`, a command line tool for acquiring temporary AWS credentials for a role assumed using the STS API via an OAuth 2.0/OpenID Connect web identity token.

The primary use case is to enable service users with identities stored in an OAuth 2.0/OpenID Connect compliant IAM service (e.g. Keycloak) to acquire access to resources via an AWS-style API (e.g. S3) by assuming a role that has access to those resources.

The MVP will be developed and refined in collaboration with users during an early access period, to address pain points and improve user experience. The goal of development during the early access period will be to produce a reference implementation, which can then be used as the basis for a clean reimplementation.

The reimplementation will provide the opportunity to shed technical debt accrued during early development and allow the adoption tooling/processes/constructs that promote security and robustness. It is anticipated that the reimplementation will be done using Rust, to produce strongly typed, memory-safe code that can be distributed as a single self-contained binary.

The MVP builds on a previous proof-of-concept (PoC) implementation. The specification for the PoC is stored in [`poc-spec.md`](./poc-spec.md), though it should be noted that this is superseded by the content of `AGENTS.md` and `CLAUDE.md`.

## Principles

To produce a reference implementation that facilitates clean reimplementation, we should follow these principles:

* Simplicity and readability of code should be preferred over optimisation
* Make use of third party libraries and packages only where this is necessary and where it serves the simplicity and readability of the code
* Avoid use of complex programming constructs where simpler ones would be sufficient
* Document all functional elements clearly and concisely using language-appropriate methods

## Tooling choices

The following should be used

* Python programming language
  * Type annotations
  * Sphinx-style docstrings
  * Unit tests written using `pytest`
  * Target Python 3.11 and higher
* `uv` package and project manager
  * Packaged application with `src`-layout
  * Script-type entry point for command line usage
* AWS Python SDK for communicating with AWS APIs
* Device authorization grant (RFC 8628) for acquiring an identity token from the IAM service
* Configuration stored in TOML format

The package is intended to be distributed to early access users for testing and feedback, so it is important to ensure portability and ease of installation:

* Possible to install using standard Python package and environment management tools (`pip`, `venv`)
* External (non-Python) dependencies should be avoided
* Compatible with major desktop operating systems: macOS, Linux, Windows

## Licensing

All files must include an [SPDX](https://spdx.dev/) header. The copyright text must be set to the appropriate copyright holder. Source files use `MIT`; documentation uses `CC-BY-SA-4.0`; other files are explicitly dedicated to the public domain and should use `CC0-1.0`. Licence texts are in `LICENSES/`. The `reuse` tool is available to check compliance:

```shell
reuse lint
```

## Testing

After making a modification to the repository, the agent should ensure that all `pytest` tests pass:

```shell
uv run pytest --verbose tests
```

If a test fails after a change, the cause of the failure should be investigated and a fix proposed.

## Linting and Formatting

After making a modification to the repository, the agent should ensure that all linting and formatting checks pass:

```shell
uv run ruff check
uv run ruff format --check
reuse lint
```

If `uv run ruff check` reports issues, run `uv run ruff check --fix` to apply automatic fixes where possible. If `uv run ruff format --check` reports issues, run `uv run ruff format` to apply formatting.
