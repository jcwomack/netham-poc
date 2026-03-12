# SPDX-FileCopyrightText: © 2026 James C. Womack
# SPDX-License-Identifier: MIT
"""Tests for netham.cli."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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


def test_no_subcommand_exits() -> None:
    """Running netham without a subcommand causes SystemExit."""
    with pytest.raises(SystemExit):
        _run_main(["netham"])
