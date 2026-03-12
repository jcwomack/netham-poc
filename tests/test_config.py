# SPDX-FileCopyrightText: © 2026 James C. Womack
# SPDX-License-Identifier: MIT
"""Tests for netham.config."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from netham.config import load_config


def _write_toml(directory: Path, filename: str, content: str) -> Path:
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


_FULL_CONFIG = (
    'issuer_url = "https://example.com"\n'
    'client_id = "myclient"\n'
    'role_arn = "arn:aws:iam::123:role/R"\n'
)


def test_loads_required_fields_from_default_file(tmp_path: Path) -> None:
    """Config is loaded from the default config file when present."""
    default = _write_toml(tmp_path, "config.toml", _FULL_CONFIG)
    nonexistent = tmp_path / "netham.toml"
    with (
        patch("netham.config.DEFAULT_CONFIG_PATH", default),
        patch("netham.config.LOCAL_CONFIG_PATH", nonexistent),
    ):
        config = load_config({})
    assert config.issuer_url == "https://example.com"
    assert config.client_id == "myclient"
    assert config.role_arn == "arn:aws:iam::123:role/R"
    assert config.sts_endpoint_url is None


def test_local_file_overrides_default_file(tmp_path: Path) -> None:
    """Values in the local config file override those in the default file."""
    default = _write_toml(tmp_path, "config.toml", _FULL_CONFIG)
    local = _write_toml(
        tmp_path, "netham.toml", 'issuer_url = "https://local.example.com"\n'
    )
    with (
        patch("netham.config.DEFAULT_CONFIG_PATH", default),
        patch("netham.config.LOCAL_CONFIG_PATH", local),
    ):
        config = load_config({})
    assert config.issuer_url == "https://local.example.com"
    assert config.client_id == "myclient"  # still from default file


def test_overrides_take_precedence_over_files(tmp_path: Path) -> None:
    """Caller-supplied overrides take precedence over config files."""
    default = _write_toml(tmp_path, "config.toml", _FULL_CONFIG)
    nonexistent = tmp_path / "netham.toml"
    with (
        patch("netham.config.DEFAULT_CONFIG_PATH", default),
        patch("netham.config.LOCAL_CONFIG_PATH", nonexistent),
    ):
        config = load_config({"client_id": "override-client"})
    assert config.client_id == "override-client"


def test_missing_required_key_exits() -> None:
    """Missing required configuration causes SystemExit."""
    nonexistent = Path("/nonexistent/path/config.toml")
    with (
        patch("netham.config.DEFAULT_CONFIG_PATH", nonexistent),
        patch("netham.config.LOCAL_CONFIG_PATH", nonexistent),
        pytest.raises(SystemExit),
    ):
        load_config({})


def test_optional_sts_endpoint_url(tmp_path: Path) -> None:
    """``sts_endpoint_url`` is loaded from config when present."""
    content = _FULL_CONFIG + 'sts_endpoint_url = "https://sts.example.com"\n'
    default = _write_toml(tmp_path, "config.toml", content)
    nonexistent = tmp_path / "netham.toml"
    with (
        patch("netham.config.DEFAULT_CONFIG_PATH", default),
        patch("netham.config.LOCAL_CONFIG_PATH", nonexistent),
    ):
        config = load_config({})
    assert config.sts_endpoint_url == "https://sts.example.com"
