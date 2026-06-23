# SPDX-FileCopyrightText: © 2026 James C. Womack
# SPDX-License-Identifier: MIT
"""Configuration loading for netham.

Configuration is resolved by merging values from multiple sources in order of
increasing precedence:

1. Default config file: ``$XDG_CONFIG_HOME/netham/config.toml`` (falling back
   to ``~/.config/netham/config.toml`` when ``XDG_CONFIG_HOME`` is unset)
2. Local config file: ``./netham.toml`` in the current working directory
3. Explicit overrides passed by the caller (e.g. from CLI arguments)
"""

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


def _default_config_path() -> Path:
    """Return the default config path, respecting the XDG Base Directory spec.

    Uses ``$XDG_CONFIG_HOME`` when set, otherwise falls back to
    ``~/.config``.

    :returns: Path to the default ``netham/config.toml`` under the XDG config
        base directory.
    """
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_config_home).expanduser() if xdg_config_home else Path.home() / ".config"
    return base / "netham" / "config.toml"


DEFAULT_CONFIG_PATH = _default_config_path()
LOCAL_CONFIG_PATH = Path("netham.toml")

_REQUIRED_KEYS = ("issuer_url", "client_id", "role_arn")


@dataclass
class Config:
    """Validated configuration for netham.

    :param issuer_url: Base URL of the OpenID Connect issuer (Keycloak realm).
    :param client_id: OAuth 2.0 client ID registered with the issuer.
    :param role_arn: ARN of the AWS IAM role to assume.
    :param sts_endpoint_url: Optional STS endpoint URL for non-AWS providers.
    :param s3_endpoint_url: Optional S3 endpoint URL for non-AWS providers.
        Defaults to ``sts_endpoint_url`` when not explicitly configured.
    :param assumed_role_duration_minutes: Optional duration for the assumed-role
        session in minutes. When ``None``, the STS default is used.
    """

    issuer_url: str
    client_id: str
    role_arn: str
    sts_endpoint_url: str | None = None
    s3_endpoint_url: str | None = None
    assumed_role_duration_minutes: int | None = None


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


def load_config(
    overrides: dict[str, str | int | None],
    local_config_path: Path = LOCAL_CONFIG_PATH,
) -> "Config":
    """Load and validate configuration from files and caller-supplied overrides.

    Values are merged in order of increasing precedence: the default config
    file, the local config file, then ``overrides``.  A human-readable error
    is printed and the process exits if any required key is missing after
    merging.

    :param overrides: Mapping of config key names to string or integer values that take
        precedence over any file-based configuration. Values of ``None`` are ignored.
    :param local_config_path: Path to the local config file. Defaults to
        :data:`LOCAL_CONFIG_PATH` (``./netham.toml``).
    :returns: Validated :class:`Config` instance.
    :raises SystemExit: If required configuration keys are missing or a value
        has an unexpected type.
    """
    merged: dict = {}
    merged.update(_load_toml_file(DEFAULT_CONFIG_PATH))
    merged.update(_load_toml_file(local_config_path))
    merged.update({k: v for k, v in overrides.items() if v is not None})

    missing = [k for k in _REQUIRED_KEYS if not merged.get(k)]
    if missing:
        sys.exit(
            f"Missing required configuration: {', '.join(missing)}\n"
            f"Set these in {DEFAULT_CONFIG_PATH} or {local_config_path}."
        )

    duration = merged.get("assumed_role_duration_minutes")
    if duration is not None and type(duration) is not int:
        sys.exit(f"assumed_role_duration_minutes must be an integer, got {type(duration).__name__!r}.")

    s3_endpoint_url = merged.get("s3_endpoint_url") or merged.get("sts_endpoint_url")
    return Config(
        issuer_url=merged["issuer_url"],
        client_id=merged["client_id"],
        role_arn=merged["role_arn"],
        sts_endpoint_url=merged.get("sts_endpoint_url"),
        s3_endpoint_url=s3_endpoint_url,
        assumed_role_duration_minutes=merged.get("assumed_role_duration_minutes"),
    )
