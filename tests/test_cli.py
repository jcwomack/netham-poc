# SPDX-FileCopyrightText: © 2026 James C. Womack
# SPDX-License-Identifier: MIT
"""Tests for netham.cli."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from netham import __version__
from netham.cli import main


def _run_main(argv: list[str]) -> None:
    with patch.object(sys, "argv", argv):
        main()


@patch("netham.cli.acquire_and_write_credentials")
@patch("netham.cli.acquire_access_token", return_value="tok")
@patch("netham.cli.load_config")
def test_auth_calls_all_steps(
    mock_load: MagicMock,
    mock_acquire: MagicMock,
    mock_write: MagicMock,
) -> None:
    """The auth subcommand calls load_config, acquire_access_token, and acquire_and_write_credentials."""
    mock_load.return_value = MagicMock()
    _run_main(["netham", "auth", "--output", "out.sh"])
    mock_load.assert_called_once()
    mock_acquire.assert_called_once_with(mock_load.return_value)
    mock_write.assert_called_once_with(mock_load.return_value, "tok", Path("out.sh"))


@patch("netham.cli.acquire_and_write_credentials")
@patch("netham.cli.acquire_access_token", return_value="tok")
@patch("netham.cli.load_config")
def test_config_arg_passed_as_local_config_path(
    mock_load: MagicMock,
    mock_acquire: MagicMock,
    mock_write: MagicMock,
    tmp_path: Path,
) -> None:
    """``--config`` is forwarded to ``load_config`` as ``local_config_path``."""
    mock_load.return_value = MagicMock()
    config_file = tmp_path / "custom.toml"
    _run_main(["netham", "--config", str(config_file), "auth"])
    _, kwargs = mock_load.call_args
    assert kwargs["local_config_path"] == config_file


@patch("netham.cli.acquire_and_write_credentials")
@patch("netham.cli.acquire_access_token", return_value="tok")
@patch("netham.cli.load_config")
def test_cli_overrides_passed_to_load_config(
    mock_load: MagicMock,
    mock_acquire: MagicMock,
    mock_write: MagicMock,
) -> None:
    """CLI config arguments are forwarded to load_config as overrides."""
    mock_load.return_value = MagicMock()
    _run_main(
        [
            "netham",
            "auth",
            "--issuer-url",
            "https://my-issuer.example.com",
            "--client-id",
            "myid",
            "--role-arn",
            "arn:aws:iam::1:role/R",
        ]
    )
    overrides = mock_load.call_args[0][0]
    assert overrides["issuer_url"] == "https://my-issuer.example.com"
    assert overrides["client_id"] == "myid"
    assert overrides["role_arn"] == "arn:aws:iam::1:role/R"


@patch("netham.cli.acquire_and_write_credentials")
@patch("netham.cli.acquire_access_token", return_value="tok")
@patch("netham.cli.load_config")
def test_default_output_filename(
    mock_load: MagicMock,
    mock_acquire: MagicMock,
    mock_write: MagicMock,
) -> None:
    """Output defaults to creds_env.sh when --output is not specified."""
    mock_load.return_value = MagicMock()
    _run_main(["netham", "auth"])
    _, _, output_path = mock_write.call_args[0]
    assert output_path == Path("creds_env.sh")


@patch("netham.cli.acquire_and_write_credentials")
@patch("netham.cli.acquire_access_token", return_value="tok")
@patch("netham.cli.load_config")
def test_assumed_role_duration_override_passed_as_int(
    mock_load: MagicMock,
    mock_acquire: MagicMock,
    mock_write: MagicMock,
) -> None:
    """--assumed-role-duration is forwarded to load_config as an integer override."""
    mock_load.return_value = MagicMock()
    _run_main(["netham", "auth", "--assumed-role-duration", "120"])
    overrides = mock_load.call_args[0][0]
    assert overrides["assumed_role_duration_minutes"] == 120
    assert isinstance(overrides["assumed_role_duration_minutes"], int)


@patch("netham.cli.acquire_and_write_credentials")
@patch("netham.cli.acquire_access_token", return_value="tok")
@patch("netham.cli.load_config")
def test_s3_endpoint_url_override_passed_to_load_config(
    mock_load: MagicMock,
    mock_acquire: MagicMock,
    mock_write: MagicMock,
) -> None:
    """--s3-endpoint-url is forwarded to load_config as an override."""
    mock_load.return_value = MagicMock()
    _run_main(["netham", "auth", "--s3-endpoint-url", "https://s3.example.com"])
    overrides = mock_load.call_args[0][0]
    assert overrides["s3_endpoint_url"] == "https://s3.example.com"


_MINIMAL_CONFIG = (
    'issuer_url = "https://issuer.example.com"\nclient_id = "myclient"\nrole_arn = "arn:aws:iam::123:role/R"\n'
)


@patch("netham.cli.acquire_and_write_credentials")
@patch("netham.cli.acquire_access_token", return_value="tok")
def test_s3_endpoint_url_defaults_to_sts_endpoint_url_from_cli(
    mock_acquire: MagicMock,
    mock_write: MagicMock,
    tmp_path: Path,
) -> None:
    """When --sts-endpoint-url is set and --s3-endpoint-url is unset, s3_endpoint_url defaults to the sts value."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(_MINIMAL_CONFIG, encoding="utf-8")
    nonexistent = tmp_path / "netham.toml"
    with patch("netham.config.DEFAULT_CONFIG_PATH", config_file):
        _run_main(["netham", "--config", str(nonexistent), "auth", "--sts-endpoint-url", "https://sts.example.com"])
    config = mock_write.call_args[0][0]
    assert config.s3_endpoint_url == "https://sts.example.com"


@patch("netham.cli.acquire_and_write_credentials")
@patch("netham.cli.acquire_access_token", return_value="tok")
def test_s3_endpoint_url_overrides_sts_endpoint_url_from_cli(
    mock_acquire: MagicMock,
    mock_write: MagicMock,
    tmp_path: Path,
) -> None:
    """When both --sts-endpoint-url and --s3-endpoint-url are set, the s3 value takes precedence."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(_MINIMAL_CONFIG, encoding="utf-8")
    nonexistent = tmp_path / "netham.toml"
    with patch("netham.config.DEFAULT_CONFIG_PATH", config_file):
        _run_main(
            [
                "netham",
                "--config",
                str(nonexistent),
                "auth",
                "--sts-endpoint-url",
                "https://sts.example.com",
                "--s3-endpoint-url",
                "https://s3.example.com",
            ]
        )
    config = mock_write.call_args[0][0]
    assert config.s3_endpoint_url == "https://s3.example.com"


def test_version_prints_version_and_exits(capsys: pytest.CaptureFixture) -> None:
    """``--version`` prints the package version to stdout and exits with code 0."""
    with pytest.raises(SystemExit) as exc_info:
        _run_main(["netham", "--version"])
    assert exc_info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_subcommand_exits() -> None:
    """Running netham without a subcommand causes SystemExit."""
    with pytest.raises(SystemExit):
        _run_main(["netham"])
