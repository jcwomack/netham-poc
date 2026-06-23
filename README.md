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

The goal of development during the early access period is to produce a reference implementation, which can then be used as the basis for a clean reimplementation. Python was chosen for this initial version to produce a clear and readable reference.

## Installation

[Python 3.11](https://www.python.org/downloads/release/python-3110/) or greater is required. It is recommended to install this package in a Python virtual environment.

### venv + pip

Using standard Python tooling, create a virtual environment

```shell
python -m venv --upgrade-deps netham-venv
```

Activate the environment

```shell
source netham-venv/bin/activate
```

Install the package into the environment

```shell
python -m pip install git+https://github.com/bristol-supercomputing/netham-early-access.git
```

This will install the latest on the `main` branch of the repository.

To install a particular tagged release, append `@tag` to the URL, e.g.

```shell
python -m pip install git+https://github.com/bristol-supercomputing/netham-early-access.git@0.1.0
```

### uv

[uv](https://docs.astral.sh/uv/) is an excellent tool that simplifies managing Python projects, packages and virtual environments. To install with `uv`, first create a virtual environment:

```shell
uv venv --prompt netham-venv
```

This will create a venv in directory `.venv` in the current directory.

Next, install the package into the virtual environment

```shell
uv pip install git+https://github.com/bristol-supercomputing/netham-early-access.git
```

To install a particular tagged release, append `@tag` to the URL, e.g.

```shell
uv pip install git+https://github.com/bristol-supercomputing/netham-early-access.git@0.1.0
```

## Usage

TODO
