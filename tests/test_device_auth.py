# SPDX-FileCopyrightText: © 2026 James C. Womack
# SPDX-License-Identifier: MIT
"""Tests for netham.device_auth."""

from unittest.mock import MagicMock, call, patch

import pytest
import requests as req_lib

from netham.config import Config
from netham.device_auth import (
    _device_auth_endpoint,
    _token_endpoint,
    poll_for_token,
    request_device_authorization,
)

_CONFIG = Config(
    issuer_url="https://issuer.example.com/realms/test",
    client_id="myclient",
    role_arn="arn:aws:iam::123:role/R",
)

_DEVICE_AUTH_RESPONSE = {
    "device_code": "dev-code-abc",
    "user_code": "ABCD-EFGH",
    "verification_uri_complete": "https://issuer.example.com/activate?code=ABCD-EFGH",
    "expires_in": 600,
    "interval": 0,  # 0 so tests don't actually sleep
}


def _make_response(ok: bool, data: dict) -> MagicMock:
    """Return a mock requests.Response."""
    resp = MagicMock()
    resp.ok = ok
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


# --- URL construction helpers ---


def test_device_auth_endpoint() -> None:
    url = _device_auth_endpoint("https://issuer.example.com/realms/test")
    assert url == (
        "https://issuer.example.com/realms/test"
        "/protocol/openid-connect/auth/device"
    )


def test_token_endpoint() -> None:
    url = _token_endpoint("https://issuer.example.com/realms/test")
    assert url == (
        "https://issuer.example.com/realms/test"
        "/protocol/openid-connect/token"
    )


# --- request_device_authorization ---


@patch("netham.device_auth.requests.post")
def test_request_device_authorization_returns_parsed_json(
    mock_post: MagicMock,
) -> None:
    """Returns the parsed JSON body on a successful response."""
    mock_post.return_value = _make_response(True, _DEVICE_AUTH_RESPONSE)
    result = request_device_authorization(_CONFIG)
    assert result["device_code"] == "dev-code-abc"
    mock_post.assert_called_once()


@patch("netham.device_auth.requests.post")
def test_request_device_authorization_http_error_exits(mock_post: MagicMock) -> None:
    """An HTTP error status causes SystemExit."""
    resp = MagicMock()
    resp.raise_for_status.side_effect = req_lib.HTTPError("500")
    mock_post.return_value = resp
    with pytest.raises(SystemExit):
        request_device_authorization(_CONFIG)


# --- poll_for_token ---


@patch("netham.device_auth.requests.post")
def test_poll_returns_token_after_pending(mock_post: MagicMock) -> None:
    """Polls through two authorization_pending responses then returns the token."""
    mock_post.side_effect = [
        _make_response(False, {"error": "authorization_pending"}),
        _make_response(False, {"error": "authorization_pending"}),
        _make_response(True, {"access_token": "mytoken"}),
    ]
    token = poll_for_token(_CONFIG, _DEVICE_AUTH_RESPONSE)
    assert token == "mytoken"
    assert mock_post.call_count == 3


@patch("netham.device_auth.requests.post")
def test_poll_slow_down_increases_interval(mock_post: MagicMock) -> None:
    """slow_down error increases the polling interval by 5 seconds."""
    mock_post.side_effect = [
        _make_response(False, {"error": "slow_down"}),
        _make_response(True, {"access_token": "tok"}),
    ]
    with patch("netham.device_auth.time.sleep") as mock_sleep:
        poll_for_token(_CONFIG, _DEVICE_AUTH_RESPONSE)
    # First sleep uses original interval (0), second uses 0+5=5
    assert mock_sleep.call_args_list == [call(0), call(5)]


@patch("netham.device_auth.requests.post")
def test_poll_expired_token_exits(mock_post: MagicMock) -> None:
    """expired_token error causes SystemExit."""
    mock_post.return_value = _make_response(False, {"error": "expired_token"})
    with pytest.raises(SystemExit):
        poll_for_token(_CONFIG, _DEVICE_AUTH_RESPONSE)


@patch("netham.device_auth.requests.post")
def test_poll_access_denied_exits(mock_post: MagicMock) -> None:
    """access_denied error causes SystemExit."""
    mock_post.return_value = _make_response(False, {"error": "access_denied"})
    with pytest.raises(SystemExit):
        poll_for_token(_CONFIG, _DEVICE_AUTH_RESPONSE)
