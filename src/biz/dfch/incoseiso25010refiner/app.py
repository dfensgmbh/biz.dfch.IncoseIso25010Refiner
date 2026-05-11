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

"""Main app module."""

from __future__ import annotations

import argparse

from rich.theme import Theme

from biz.dfch.logging import log
from biz.dfch.version import Version

from .constant import Constant


class App:  # pylint: disable=R0903
    """The application."""

    _VERSION_REQUIRED_MAJOR = 3
    _VERSION_REQUIRED_MINOR = 11

    _rule_theme = Theme(
        {
            # "markdown.h1": "bold magenta",
            # "markdown.h2": "bold cyan",
            "markdown.code": "red",
            # Not really documented. We take the definition from rich:
            # DEFAULT_STYLES: Dict[str, Style]
            # "markdown.link_url": Style(color="blue", underline=True), ...
            "markdown.link_url": "cyan",
        }
    )

    _parser: argparse.ArgumentParser
    _args: argparse.Namespace

    def __init__(self, parser: argparse.ArgumentParser):

        Version().ensure_minimum_version(
            self._VERSION_REQUIRED_MAJOR, self._VERSION_REQUIRED_MINOR
        )

        assert isinstance(parser, argparse.ArgumentParser)
        self._parser = parser
        self._args = parser.parse_args()

    def on_dictionary(self) -> None:
        """This method processes the `dictionary` argument."""
        ...

    def invoke(self) -> None:
        """Main entry point for this class."""

        # Set the effective log level.
        from .args import Args  # pylint: disable=C0415

        log_level = Args.get_effective_log_level_name(self._args)
        import logging  # pylint: disable=C0415

        for handler in logging.getLogger().handlers:
            handler.setLevel(log_level)

        # Print program information.
        log.debug(self._parser.description)
        print(self._parser.description)
        log.debug(self._parser.epilog)
        print(self._parser.epilog)

        if self._args.command == "dictionary":

            self.on_dictionary(
            )
            return

        self.on_dictionary(
        )
