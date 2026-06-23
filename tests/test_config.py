# SPDX-FileCopyrightText: © 2026 James C. Womack
# SPDX-License-Identifier: MIT
"""Tests for netham.config."""

from pathlib import Path
from unittest.mock import patch

import pytest

from netham.config import _default_config_path, load_config


def _write_toml(directory: Path, filename: str, content: str) -> Path:
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


_FULL_CONFIG = 'issuer_url = "https://example.com"\nclient_id = "myclient"\nrole_arn = "arn:aws:iam::123:role/R"\n'


def test_loads_required_fields_from_default_file(tmp_path: Path) -> None:
    """Config is loaded from the default config file when present."""
    default = _write_toml(tmp_path, "config.toml", _FULL_CONFIG)
    nonexistent = tmp_path / "netham.toml"
    with patch("netham.config.DEFAULT_CONFIG_PATH", default):
        config = load_config({}, local_config_path=nonexistent)
    assert config.issuer_url == "https://example.com"
    assert config.client_id == "myclient"
    assert config.role_arn == "arn:aws:iam::123:role/R"
    assert config.sts_endpoint_url is None


def test_local_file_overrides_default_file(tmp_path: Path) -> None:
    """Values in the local config file override those in the default file."""
    default = _write_toml(tmp_path, "config.toml", _FULL_CONFIG)
    local = _write_toml(tmp_path, "netham.toml", 'issuer_url = "https://local.example.com"\n')
    with patch("netham.config.DEFAULT_CONFIG_PATH", default):
        config = load_config({}, local_config_path=local)
    assert config.issuer_url == "https://local.example.com"
    assert config.client_id == "myclient"  # still from default file


def test_overrides_take_precedence_over_files(tmp_path: Path) -> None:
    """Caller-supplied overrides take precedence over config files."""
    default = _write_toml(tmp_path, "config.toml", _FULL_CONFIG)
    nonexistent = tmp_path / "netham.toml"
    with patch("netham.config.DEFAULT_CONFIG_PATH", default):
        config = load_config({"client_id": "override-client"}, local_config_path=nonexistent)
    assert config.client_id == "override-client"


def test_missing_required_key_exits() -> None:
    """Missing required configuration causes SystemExit."""
    nonexistent = Path("/nonexistent/path/config.toml")
    with (
        patch("netham.config.DEFAULT_CONFIG_PATH", nonexistent),
        pytest.raises(SystemExit),
    ):
        load_config({}, local_config_path=nonexistent)


def test_optional_sts_endpoint_url(tmp_path: Path) -> None:
    """``sts_endpoint_url`` is loaded from config when present."""
    content = _FULL_CONFIG + 'sts_endpoint_url = "https://sts.example.com"\n'
    default = _write_toml(tmp_path, "config.toml", content)
    nonexistent = tmp_path / "netham.toml"
    with patch("netham.config.DEFAULT_CONFIG_PATH", default):
        config = load_config({}, local_config_path=nonexistent)
    assert config.sts_endpoint_url == "https://sts.example.com"


def test_assumed_role_duration_minutes_loaded_from_config(tmp_path: Path) -> None:
    """``assumed_role_duration_minutes`` is loaded from config as an integer."""
    content = _FULL_CONFIG + "assumed_role_duration_minutes = 120\n"
    default = _write_toml(tmp_path, "config.toml", content)
    nonexistent = tmp_path / "netham.toml"
    with patch("netham.config.DEFAULT_CONFIG_PATH", default):
        config = load_config({}, local_config_path=nonexistent)
    assert config.assumed_role_duration_minutes == 120


def test_assumed_role_duration_minutes_wrong_type_exits(tmp_path: Path) -> None:
    """A non-integer value for ``assumed_role_duration_minutes`` causes SystemExit."""
    content = _FULL_CONFIG + 'assumed_role_duration_minutes = "120"\n'
    default = _write_toml(tmp_path, "config.toml", content)
    nonexistent = tmp_path / "netham.toml"
    with (
        patch("netham.config.DEFAULT_CONFIG_PATH", default),
        pytest.raises(SystemExit),
    ):
        load_config({}, local_config_path=nonexistent)


def test_assumed_role_duration_minutes_defaults_to_none(tmp_path: Path) -> None:
    """``assumed_role_duration_minutes`` defaults to ``None`` when absent from config."""
    default = _write_toml(tmp_path, "config.toml", _FULL_CONFIG)
    nonexistent = tmp_path / "netham.toml"
    with patch("netham.config.DEFAULT_CONFIG_PATH", default):
        config = load_config({}, local_config_path=nonexistent)
    assert config.assumed_role_duration_minutes is None


def test_s3_endpoint_url_explicit(tmp_path: Path) -> None:
    """``s3_endpoint_url`` is loaded from config when explicitly set."""
    content = _FULL_CONFIG + 's3_endpoint_url = "https://s3.example.com"\n'
    default = _write_toml(tmp_path, "config.toml", content)
    nonexistent = tmp_path / "netham.toml"
    with patch("netham.config.DEFAULT_CONFIG_PATH", default):
        config = load_config({}, local_config_path=nonexistent)
    assert config.s3_endpoint_url == "https://s3.example.com"


def test_s3_endpoint_url_defaults_to_none_when_neither_set(tmp_path: Path) -> None:
    """``s3_endpoint_url`` is ``None`` when neither ``s3_endpoint_url`` nor ``sts_endpoint_url`` is set."""
    default = _write_toml(tmp_path, "config.toml", _FULL_CONFIG)
    nonexistent = tmp_path / "netham.toml"
    with patch("netham.config.DEFAULT_CONFIG_PATH", default):
        config = load_config({}, local_config_path=nonexistent)
    assert config.s3_endpoint_url is None


def test_s3_endpoint_url_falls_back_to_sts_endpoint_url(tmp_path: Path) -> None:
    """``s3_endpoint_url`` falls back to ``sts_endpoint_url`` when not explicitly set."""
    content = _FULL_CONFIG + 'sts_endpoint_url = "https://sts.example.com"\n'
    default = _write_toml(tmp_path, "config.toml", content)
    nonexistent = tmp_path / "netham.toml"
    with patch("netham.config.DEFAULT_CONFIG_PATH", default):
        config = load_config({}, local_config_path=nonexistent)
    assert config.s3_endpoint_url == "https://sts.example.com"


def test_s3_endpoint_url_takes_precedence_over_sts_endpoint_url(tmp_path: Path) -> None:
    """An explicit ``s3_endpoint_url`` takes precedence over ``sts_endpoint_url``."""
    content = (
        _FULL_CONFIG + 'sts_endpoint_url = "https://sts.example.com"\n' + 's3_endpoint_url = "https://s3.example.com"\n'
    )
    default = _write_toml(tmp_path, "config.toml", content)
    nonexistent = tmp_path / "netham.toml"
    with patch("netham.config.DEFAULT_CONFIG_PATH", default):
        config = load_config({}, local_config_path=nonexistent)
    assert config.s3_endpoint_url == "https://s3.example.com"


def test_default_config_path_uses_xdg_config_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``_default_config_path`` uses ``XDG_CONFIG_HOME`` when set."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert _default_config_path() == tmp_path / "netham" / "config.toml"


def test_default_config_path_falls_back_to_home_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """``_default_config_path`` falls back to ``~/.config`` when ``XDG_CONFIG_HOME`` is unset."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert _default_config_path() == Path.home() / ".config" / "netham" / "config.toml"


def test_default_config_path_expands_tilde_in_xdg_config_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """``_default_config_path`` expands ``~`` in ``XDG_CONFIG_HOME``."""
    monkeypatch.setenv("XDG_CONFIG_HOME", "~/.config/custom")
    assert _default_config_path() == Path.home() / ".config" / "custom" / "netham" / "config.toml"
