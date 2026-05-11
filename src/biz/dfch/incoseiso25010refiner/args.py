# Copyright (c) 2025 Ronald Rink, http://d-fens.ch
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

    def __init__(self):

        common = argparse.ArgumentParser(add_help=False)
        common.add_argument(
            "--log-level",
            "-l",
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

        self._parser = argparse.ArgumentParser(
            description=f"{Constant.PROG_NAME}, "
            f"v{Constant._VERSION}"
            ". "
            "An INCOSE and ISO25010 requirements refiner.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            prog=Constant.PROG_NAME,
            epilog="Copyright 2025 Ronald Rink, "
            "https://github.com/dfensgmbh/biz.dfch.IncoseIso25010Refiner"
            ". "
            "Licensed under AGPLv3.",
        )

        subparsers = self._parser.add_subparsers(
            dest="command", help="Available commands."
        )

        dictionary_parser = subparsers.add_parser(
            "default", parents=[common], help="The default command."
        )

        dictionary_parser.add_argument(
            "-i",
            "--input",
            nargs="+",
            metavar="PATH",
            default=[],
            required=False,
            help="A list of dictionary files to read entries from (full path).",
        )

        dictionary_parser.add_argument(
            "--ste100",
            dest="use_ste100",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Load built-in STE-100 words.",
        )

        dictionary_parser.add_argument(
            "--tn",
            dest="use_technical_nouns",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Load built-in Technical Nouns (TN).",
        )

        dictionary_parser.add_argument(
            "--tv",
            dest="use_technical_verbs",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Load built-in Technical Verbs (TV).",
        )

        dictionary_parser.add_argument(
            "--no-random-word",
            action="store_true",
            help="Prevent display of random word at startup.",
        )

    @staticmethod
    def get_effective_log_level_name(args) -> str:
        """Returns the effective log level name."""

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
