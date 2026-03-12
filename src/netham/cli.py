# SPDX-FileCopyrightText: © 2026 James C. Womack
# SPDX-License-Identifier: MIT
"""Command-line interface for netham.

Provides the ``netham`` entry point with an ``auth`` subcommand that runs the
Device Authorization Grant flow and writes temporary AWS credentials to a file.
"""

import argparse
from pathlib import Path

from netham.config import load_config
from netham.credentials import acquire_and_write_credentials
from netham.device_auth import acquire_access_token


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the netham CLI.

    :returns: Configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        prog="netham",
        description="Acquire temporary AWS credentials via OpenID Connect.",
    )
    subparsers = parser.add_subparsers(title="subcommands", required=True)

    auth_parser = subparsers.add_parser(
        "auth",
        help="Authenticate and write temporary AWS credentials to a file.",
    )
    auth_parser.add_argument(
        "--output",
        metavar="FILE",
        default="creds_env.sh",
        help="Path for the credentials shell script (default: creds_env.sh).",
    )
    auth_parser.add_argument(
        "--issuer-url",
        metavar="URL",
        dest="issuer_url",
        help="OpenID Connect issuer base URL (overrides config file).",
    )
    auth_parser.add_argument(
        "--client-id",
        metavar="ID",
        dest="client_id",
        help="OAuth 2.0 client ID (overrides config file).",
    )
    auth_parser.add_argument(
        "--role-arn",
        metavar="ARN",
        dest="role_arn",
        help="AWS IAM role ARN to assume (overrides config file).",
    )
    auth_parser.add_argument(
        "--sts-endpoint-url",
        metavar="URL",
        dest="sts_endpoint_url",
        help="STS endpoint URL for non-AWS providers (overrides config file).",
    )
    auth_parser.set_defaults(func=_cmd_auth)

    return parser


def _cmd_auth(args: argparse.Namespace) -> None:
    """Execute the ``auth`` subcommand.

    Loads configuration (with any CLI overrides applied), runs the Device
    Authorization Grant flow, and writes the credentials script.

    :param args: Parsed arguments from the ``auth`` subparser.
    """
    overrides = {
        "issuer_url": args.issuer_url,
        "client_id": args.client_id,
        "role_arn": args.role_arn,
        "sts_endpoint_url": args.sts_endpoint_url,
    }
    config = load_config(overrides)
    access_token = acquire_access_token(config)
    acquire_and_write_credentials(config, access_token, Path(args.output))


def main() -> None:
    """Entry point for the ``netham`` command.

    Parses command-line arguments and dispatches to the appropriate subcommand
    handler.
    """
    parser = _build_parser()
    args = parser.parse_args()
    args.func(args)
