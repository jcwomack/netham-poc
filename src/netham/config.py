# SPDX-FileCopyrightText: © 2026 James C. Womack
# SPDX-License-Identifier: MIT
"""Configuration loading for netham.

Configuration is resolved by merging values from multiple sources in order of
increasing precedence:

1. Default config file: ``~/.config/netham/config.toml``
2. Local config file: ``./netham.toml`` in the current working directory
3. Explicit overrides passed by the caller (e.g. from CLI arguments)
"""

import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "netham" / "config.toml"
LOCAL_CONFIG_PATH = Path("netham.toml")

_REQUIRED_KEYS = ("issuer_url", "client_id", "role_arn")


@dataclass
class Config:
    """Validated configuration for netham.

    :param issuer_url: Base URL of the OpenID Connect issuer (Keycloak realm).
    :param client_id: OAuth 2.0 client ID registered with the issuer.
    :param role_arn: ARN of the AWS IAM role to assume.
    :param sts_endpoint_url: Optional STS endpoint URL for non-AWS providers.
    """

    issuer_url: str
    client_id: str
    role_arn: str
    sts_endpoint_url: str | None = None


def _load_toml_file(path: Path) -> dict:
    """Load a TOML file and return its contents as a dictionary.

    Returns an empty dictionary if the file does not exist.

    :param path: Path to the TOML file.
    :returns: Parsed TOML contents, or ``{}`` if the file is absent.
    """
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def load_config(overrides: dict[str, str]) -> "Config":
    """Load and validate configuration from files and caller-supplied overrides.

    Values are merged in order of increasing precedence: the default config
    file, the local config file, then ``overrides``.  A human-readable error
    is printed and the process exits if any required key is missing after
    merging.

    :param overrides: Mapping of config key names to string values that take
        precedence over any file-based configuration.
    :returns: Validated :class:`Config` instance.
    :raises SystemExit: If required configuration keys are missing.
    """
    merged: dict = {}
    merged.update(_load_toml_file(DEFAULT_CONFIG_PATH))
    merged.update(_load_toml_file(LOCAL_CONFIG_PATH))
    merged.update({k: v for k, v in overrides.items() if v is not None})

    missing = [k for k in _REQUIRED_KEYS if not merged.get(k)]
    if missing:
        sys.exit(
            f"Missing required configuration: {', '.join(missing)}\n"
            f"Set these in {DEFAULT_CONFIG_PATH} or {LOCAL_CONFIG_PATH}."
        )

    return Config(
        issuer_url=merged["issuer_url"],
        client_id=merged["client_id"],
        role_arn=merged["role_arn"],
        sts_endpoint_url=merged.get("sts_endpoint_url"),
    )
