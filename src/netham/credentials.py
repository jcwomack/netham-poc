# SPDX-FileCopyrightText: © 2026 James C. Womack
# SPDX-License-Identifier: MIT
"""AWS credential acquisition and output file writing.

Handles decoding the JWT access token to extract the user subject, calling the
AWS STS AssumeRoleWithWebIdentity endpoint, and writing the resulting temporary
credentials to a bash export script.
"""

import base64
import json
import sys
from pathlib import Path
from shlex import quote

import boto3
import botocore.exceptions
from botocore import UNSIGNED
from botocore.config import Config as BotocoreConfig

from netham.config import Config

# Minimum DurationSeconds accepted by assume_role_with_web_identity(), converted to minutes.
_MIN_DURATION_MINUTES = 15


def decode_jwt_payload(token: str) -> dict:
    """Decode the payload of a JWT without verifying the signature.

    Extracts the claims from the base64url-encoded payload segment of the token.
    Not verifying signature is fine since not used for sensitive reasons such
    as access control.

    :param token: JWT access token string.
    :returns: Parsed payload claims as a dictionary.
    :raises SystemExit: If the token is malformed.
    """
    parts = token.split(".")
    if len(parts) != 3:
        sys.exit("Malformed access token: expected three dot-separated segments.")
    payload_b64 = parts[1]
    # base64url encoding omits padding; restore it before decoding
    payload_b64 += "=" * (-len(payload_b64) % 4)
    try:
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)
    except (ValueError, json.JSONDecodeError) as exc:
        sys.exit(f"Failed to decode access token payload: {exc}")


def extract_sub(payload: dict) -> str:
    """Extract the subject identifier from JWT payload claims.

    :param payload: Decoded JWT payload dictionary.
    :returns: The value of the ``sub`` claim.
    :raises SystemExit: If the ``sub`` claim is absent.
    """
    sub = payload.get("sub")
    if not sub:
        sys.exit("Access token does not contain a 'sub' claim.")
    return sub


def assume_role(config: Config, access_token: str, role_session_name: str) -> dict:
    """Call AWS STS AssumeRoleWithWebIdentity using the provided token.

    :param config: Loaded netham configuration.
    :param access_token: JWT access token to use as the web identity.
    :param role_session_name: Name tag to apply to the assumed-role session.
    :returns: Credentials dictionary with keys ``AccessKeyId``,
        ``SecretAccessKey``, and ``SessionToken``.
    :raises SystemExit: If the duration is below the minimum allowed value or
        the STS call fails.
    """
    if config.assumed_role_duration_minutes is not None:
        if config.assumed_role_duration_minutes < _MIN_DURATION_MINUTES:
            sys.exit(
                f"assumed_role_duration_minutes must be at least {_MIN_DURATION_MINUTES}"
                f" (got {config.assumed_role_duration_minutes})."
            )
    client = boto3.client(
        "sts",
        endpoint_url=config.sts_endpoint_url,
        config=BotocoreConfig(signature_version=UNSIGNED),
    )
    kwargs: dict = {
        "RoleArn": config.role_arn,
        "RoleSessionName": role_session_name,
        "WebIdentityToken": access_token,
    }
    if config.assumed_role_duration_minutes is not None:
        kwargs["DurationSeconds"] = config.assumed_role_duration_minutes * 60
    try:
        response = client.assume_role_with_web_identity(**kwargs)
    except botocore.exceptions.ClientError as exc:
        sys.exit(f"STS AssumeRoleWithWebIdentity failed: {exc}")
    return response["Credentials"]


def write_credentials_script(credentials: dict, output_path: Path, s3_endpoint_url: str | None = None) -> None:
    """Write a bash script that exports AWS credentials as environment variables.

    The output file is set to mode 0o600 (owner read/write only).

    :param credentials: Credentials dict from :func:`assume_role`.
    :param output_path: Destination path for the shell script.
    :param s3_endpoint_url: Optional S3 endpoint URL to export as
        ``AWS_ENDPOINT_URL_S3``.
    """
    content = (
        "#!/bin/bash\n"
        f"export AWS_ACCESS_KEY_ID={quote(credentials['AccessKeyId'])}\n"
        f"export AWS_SECRET_ACCESS_KEY={quote(credentials['SecretAccessKey'])}\n"
        f"export AWS_SESSION_TOKEN={quote(credentials['SessionToken'])}\n"
    )
    if s3_endpoint_url is not None:
        content += f"export AWS_ENDPOINT_URL_S3={quote(s3_endpoint_url)}\n"
    output_path.write_text(content, encoding="utf-8")
    output_path.chmod(0o600)


def acquire_and_write_credentials(config: Config, access_token: str, output_path: Path) -> None:
    """Orchestrate credential acquisition and output file writing.

    Decodes the access token to obtain the user subject, constructs a role
    session name, calls STS to assume the role, writes the credentials script,
    and prints a success message.

    :param config: Loaded netham configuration.
    :param access_token: JWT access token from the device authorization flow.
    :param output_path: Destination path for the credentials shell script.
    """
    payload = decode_jwt_payload(access_token)
    sub = extract_sub(payload)
    role_session_name = f"{sub}-session"
    credentials = assume_role(config, access_token, role_session_name)
    write_credentials_script(credentials, output_path, s3_endpoint_url=config.s3_endpoint_url)
    print(
        f"S3 temporary access credentials acquired for user {sub}."
        f" Add these to your environment by running\n\nsource {output_path}\n"
    )
