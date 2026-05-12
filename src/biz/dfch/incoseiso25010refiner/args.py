# Copyright (c) 2026 Ronald Rink, http://d-fens.ch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Arg parsing module."""

from __future__ import annotations

import argparse
from pathlib import Path
import uuid

from .chat.chat_config import Providers
from .constant import Constant


class Args:
    """
    Definition and handling of supported command line arguments.
    """

    _parser: argparse.ArgumentParser

    LOG_LEVEL_CHOICES = [
        "CRITICAL",
        "FATAL",
        "ERROR",
        "WARNING",
        "WARN",
        "INFO",
        "DEBUG",
        "NOTSET",
    ]
    _DEFAULT_LOG_LEVEL = "ERROR"

    _DEFAULT_BASE_URL = "https://routellm.abacus.ai/v1"

    @staticmethod
    def _ensure_non_empty_string(value: str) -> str:
        if not value or not value.strip():
            raise argparse.ArgumentTypeError("Value cannot be null or empty.")
        return value

    def __init__(self):

        common = argparse.ArgumentParser(add_help=False)
        common.add_argument(
            "-l",
            "--log-level",
            dest="log_level",
            choices=self.LOG_LEVEL_CHOICES,
            help=f"Logging level (default: {self._DEFAULT_LOG_LEVEL}).",
        )
        common.add_argument(
            "-v",
            action="count",
            default=0,
            help="Increase verbosity (-v = WARNING, -vv = INFO, -vvv = DEBUG).",
        )
        common.add_argument(
            "-id",
            "--session-id",
            dest="session",
            type=self._ensure_non_empty_string,
            default=str(uuid.uuid4()),
            metavar="ID",
            help="Session id (default: pseudo-random generated GUID).",
        )
        common.add_argument(
            "-o",
            "--output-dir",
            dest="output",
            type=lambda path: Args._validate_dir(common, path),
            default=".",
            metavar="PATH",
            help="Output directory (default: current working directory).",
        )

        self._parser = argparse.ArgumentParser(
            description=f"{Constant.PROG_NAME}, "
            f"v{Constant._VERSION}"
            ". "
            "An INCOSE and ISO25010 requirements refiner.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            prog=Constant.PROG_NAME,
            epilog="Copyright 2025-2026 d-fens GmbH, Ronald Rink, "
            "https://github.com/dfensgmbh/biz.dfch.IncoseIso25010Refiner"
            ". "
            "Licensed under AGPLv3.",
        )

        subparsers = self._parser.add_subparsers(
            dest="command", help="Available commands."
        )

        query_parser = subparsers.add_parser(
            "query",
            parents=[common],
            help="Operate an LLM API.",
        )
        query_parser.add_argument(
            "--provider",
            dest="provider",
            choices=Providers,
            default=Providers.DEFAULT,
            help=f"The chat provider to use (default: {Providers.DEFAULT}).",
        )
        prompt_group = query_parser.add_mutually_exclusive_group(required=True)
        prompt_group.add_argument(
            "-p",
            "--prompt",
            "--prompt-text",
            dest="prompt",
            metavar="TEXT",
            help="The prompt text to send to the LLM.",
        )
        prompt_group.add_argument(
            "-pf",
            "--file",
            "--prompt-file",
            dest="prompt",
            metavar="PATH",
            type=lambda e: Args._get_file_content(query_parser, e),
            help="The prompt file to send to the LLM.",
        )
        query_parser.add_argument(
            "-t",
            "--template",
            dest="template",
            default=None,
            metavar="PATH",
            type=lambda e: Args._validate_file(query_parser, e),
            help=(
                "Path to a local template file to load and send with the "
                "prompt."
            ),
        )
        query_parser.add_argument(
            "--api-token",
            dest="api_token",
            default="",
            metavar="TOKEN",
            help=(
                "API bearer token. "
                "If not specified, use CHAT_API_TOKEN environment variable."
            ),
        )
        query_parser.add_argument(
            "-uri",
            "--base-url",
            dest="base_url",
            default="",
            metavar="URL",
            help="API base URL (default depends on specified provider).",
        )
        query_parser.add_argument(
            "-m",
            "--model",
            dest="model",
            default="",
            metavar="MODEL",
            help="LLM model to use (default depends on specified provider).",
        )
        query_parser.add_argument(
            "--temperature",
            dest="temperature",
            type=float,
            default=0.5,
            metavar="FLOAT",
            help="Sampling temperature (0..1). Optional.",
        )
        query_parser.add_argument(
            "--max-tokens",
            dest="max_tokens",
            type=int,
            default=None,
            metavar="INT",
            help="Maximum number of tokens in the response. Optional.",
        )

    @staticmethod
    def _get_file_content(parser, path) -> str:
        """Examine if the argument is a valid file name."""

        assert isinstance(parser, argparse.ArgumentParser), type(parser)
        assert isinstance(path, str), type(path)

        full_name = Path(path).expanduser()
        if not full_name.exists():
            parser.error(f"File '{full_name}' does not exist.")
        if not full_name.is_file():
            parser.error(f"File '{full_name}' is not a file.")

        return full_name.read_text(encoding="utf-8")

    @staticmethod
    def _validate_file(parser, path) -> str:
        """Examine if the argument is a valid file name."""

        assert isinstance(parser, argparse.ArgumentParser), type(parser)
        assert isinstance(path, str), type(path)

        full_name = Path(path).expanduser()
        if not full_name.exists():
            parser.error(f"File '{full_name}' does not exist.")
        if not full_name.is_file():
            parser.error(f"File '{full_name}' is not a file.")

        return str(full_name.resolve())

    @staticmethod
    def _validate_dir(parser, path) -> str:
        """Examine if the argument is a valid directory path."""

        assert isinstance(parser, argparse.ArgumentParser), type(parser)
        assert isinstance(path, str), type(path)

        full_name = Path(path).expanduser()
        if not full_name.exists():
            parser.error(f"Directory '{full_name}' does not exist.")
        if not full_name.is_dir():
            parser.error(f"Path '{full_name}' is not a directory.")

        return str(full_name.resolve())

    @staticmethod
    def get_effective_log_level_name(args) -> str:
        """Return the effective log level name."""

        result = Args._DEFAULT_LOG_LEVEL

        # Explicit specification of --log-level takes precedence.
        if hasattr(args, "log_level") and args.log_level:
            result = args.log_level.upper()
            return result

        # Return default log level if no "-v" is specified.
        if not hasattr(args, "v"):
            return result

        # Otherwise map verbosity count to log level.
        if args.v >= 3:
            result = "DEBUG"
            return result

        if args.v == 2:
            result = "INFO"
            return result

        if args.v == 1:
            result = "WARNING"
            return result

        return result

    def invoke(self) -> argparse.ArgumentParser:
        """
        Initialise supported command line arguments.
        """

        return self._parser
