# SPDX-FileCopyrightText: © 2026 James C. Womack
# SPDX-License-Identifier: MIT
"""OAuth 2.0 Device Authorization Grant flow (RFC 8628).

Implements the full device authorization grant: initiating the flow,
displaying the verification URI to the user, and polling the token endpoint
until authorization is granted or denied.
"""

import sys
import time

import requests

from netham.config import Config


def _device_auth_endpoint(issuer_url: str) -> str:
    """Construct the device authorization endpoint URL from the issuer URL.

    :param issuer_url: Base URL of the OpenID Connect issuer.
    :returns: Device authorization endpoint URL.
    """
    return f"{issuer_url}/protocol/openid-connect/auth/device"


def _token_endpoint(issuer_url: str) -> str:
    """Construct the token endpoint URL from the issuer URL.

    :param issuer_url: Base URL of the OpenID Connect issuer.
    :returns: Token endpoint URL.
    """
    return f"{issuer_url}/protocol/openid-connect/token"


def request_device_authorization(config: Config) -> dict:
    """Send the initial device authorization request to the issuer.

    :param config: Loaded netham configuration.
    :returns: Parsed JSON response containing ``device_code``, ``user_code``,
        ``verification_uri_complete``, ``expires_in``, and ``interval``.
    :raises SystemExit: If the HTTP request fails or returns an error status.
    """
    url = _device_auth_endpoint(config.issuer_url)
    try:
        response = requests.post(url, data={"client_id": config.client_id})
        response.raise_for_status()
    except requests.HTTPError as exc:
        sys.exit(f"Device authorization request failed: {exc}")
    return response.json()


def poll_for_token(config: Config, device_auth_response: dict) -> str:
    """Poll the token endpoint until the user completes authorization.

    Implements the polling behaviour specified in :rfc:`8628` §3.5, including
    handling of ``authorization_pending`` and ``slow_down`` error responses.

    :param config: Loaded netham configuration.
    :param device_auth_response: Response dict from
        :func:`request_device_authorization`.
    :returns: Access token string on successful authorization.
    :raises SystemExit: On ``access_denied``, ``expired_token``, or timeout.
    """
    url = _token_endpoint(config.issuer_url)
    device_code = device_auth_response["device_code"]
    interval = device_auth_response.get("interval", 5)
    expires_in = device_auth_response["expires_in"]
    deadline = time.monotonic() + expires_in

    while time.monotonic() < deadline:
        time.sleep(interval)
        try:
            response = requests.post(
                url,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id": config.client_id,
                    "device_code": device_code,
                },
            )
        except requests.RequestException as exc:
            sys.exit(f"Token request failed: {exc}")

        if response.ok:
            return response.json()["access_token"]

        error = response.json().get("error")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval += 5
            continue
        if error == "access_denied":
            sys.exit("Authorization denied by user.")
        if error == "expired_token":
            sys.exit("Device code expired. Please run netham auth again.")
        sys.exit(f"Unexpected error from token endpoint: {error}")

    sys.exit("Timed out waiting for authorization.")


def acquire_access_token(config: Config) -> str:
    """Orchestrate the Device Authorization Grant flow.

    Sends the device authorization request, prints the verification URI for
    the user to open in a browser, then polls for the access token.

    :param config: Loaded netham configuration.
    :returns: Access token string.
    """
    device_auth_response = request_device_authorization(config)
    verification_uri = device_auth_response.get(
        "verification_uri_complete", device_auth_response.get("verification_uri", "")
    )
    print(f"Open this URL in your browser:\n\n{verification_uri}\n")
    return poll_for_token(config, device_auth_response)
