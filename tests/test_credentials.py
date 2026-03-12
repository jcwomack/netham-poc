# SPDX-FileCopyrightText: © 2026 James C. Womack
# SPDX-License-Identifier: MIT
"""Tests for netham.credentials."""

import base64
import json
import os
import stat
from pathlib import Path
from unittest.mock import MagicMock, patch

import botocore.exceptions
import pytest

from netham.config import Config
from netham.credentials import (
    assume_role,
    decode_jwt_payload,
    extract_sub,
    write_credentials_script,
)

_CONFIG = Config(
    issuer_url="https://issuer.example.com/realms/test",
    client_id="myclient",
    role_arn="arn:aws:iam::123:role/R",
)

_CREDENTIALS = {
    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "SessionToken": "AQoDYXdzEJr...",
}


def _make_jwt(payload: dict) -> str:
    """Build a minimal fake JWT with the given payload."""
    header_b64 = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    payload_b64 = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    )
    return f"{header_b64}.{payload_b64}.fakesignature"


# --- decode_jwt_payload ---


def test_decode_jwt_payload_round_trip() -> None:
    """Payload round-trips through encode and decode correctly."""
    payload = {"sub": "user123", "preferred_username": "alice"}
    result = decode_jwt_payload(_make_jwt(payload))
    assert result["sub"] == "user123"
    assert result["preferred_username"] == "alice"


def test_decode_jwt_payload_malformed_token_exits() -> None:
    """A token without three segments causes SystemExit."""
    with pytest.raises(SystemExit):
        decode_jwt_payload("not.a.valid.jwt.here.extra")


def test_decode_jwt_payload_missing_padding_handled() -> None:
    """Decoding succeeds even when base64 padding chars are absent."""
    result = decode_jwt_payload(_make_jwt({"sub": "x"}))
    assert result["sub"] == "x"


# --- extract_sub ---


def test_extract_sub_returns_sub() -> None:
    assert extract_sub({"sub": "user42"}) == "user42"


def test_extract_sub_missing_exits() -> None:
    with pytest.raises(SystemExit):
        extract_sub({})


# --- assume_role ---


@patch("netham.credentials.boto3.client")
def test_assume_role_returns_credentials(mock_boto_client: MagicMock) -> None:
    """STS response credentials are returned on success."""
    mock_sts = MagicMock()
    mock_sts.assume_role_with_web_identity.return_value = {"Credentials": _CREDENTIALS}
    mock_boto_client.return_value = mock_sts

    result = assume_role(_CONFIG, "mytoken", "user42-session")

    mock_boto_client.assert_called_once_with("sts", endpoint_url=None)
    mock_sts.assume_role_with_web_identity.assert_called_once_with(
        RoleArn=_CONFIG.role_arn,
        RoleSessionName="user42-session",
        WebIdentityToken="mytoken",
    )
    assert result["AccessKeyId"] == _CREDENTIALS["AccessKeyId"]


@patch("netham.credentials.boto3.client")
def test_assume_role_client_error_exits(mock_boto_client: MagicMock) -> None:
    """A botocore ClientError causes SystemExit."""
    mock_sts = MagicMock()
    mock_sts.assume_role_with_web_identity.side_effect = (
        botocore.exceptions.ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "AssumeRoleWithWebIdentity",
        )
    )
    mock_boto_client.return_value = mock_sts
    with pytest.raises(SystemExit):
        assume_role(_CONFIG, "token", "session")


# --- write_credentials_script ---


def test_write_credentials_script_file_contents(tmp_path: Path) -> None:
    """Output file contains the expected export statements."""
    output = tmp_path / "creds_env.sh"
    write_credentials_script(_CREDENTIALS, output)
    content = output.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash\n")
    assert 'export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"' in content
    assert (
        'export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"'
        in content
    )
    assert 'export AWS_SESSION_TOKEN="AQoDYXdzEJr..."' in content


def test_write_credentials_script_file_permissions(tmp_path: Path) -> None:
    """Output file is set to mode 0o600."""
    output = tmp_path / "creds_env.sh"
    write_credentials_script(_CREDENTIALS, output)
    assert stat.S_IMODE(os.stat(output).st_mode) == 0o600
