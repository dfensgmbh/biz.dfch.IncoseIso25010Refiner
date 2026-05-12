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

"""Main app module."""

from __future__ import annotations

import argparse

from rich.theme import Theme

from biz.dfch.logging import log
from biz.dfch.version import Version

from .chat.chat_config import ChatConfig
from .chat.chat_client_factory import ChatClientFactory


class App:  # pylint: disable=R0903
    """The application."""

    _VERSION_REQUIRED_MAJOR = 3
    _VERSION_REQUIRED_MINOR = 13

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

    def on_default(self) -> None:
        """This method processes the `default` argument."""
        ...

    def on_query(self, cfg: ChatConfig) -> None:
        """This method processes the `query` argument."""

        assert isinstance(cfg, ChatConfig)

        from rich.console import Console
        from rich.markdown import Markdown
        from rich.table import Table
        from rich.json import JSON

        console = Console()
        table = Table(
            title="Chat Configuration",
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("Setting", style="bold")
        table.add_column("Value")

        table.add_row("prompt", cfg.prompt)
        table.add_row("template", cfg.template)
        table.add_row("session", cfg.session_id)
        table.add_row("output", cfg.output_path)
        table.add_row("provider", cfg.provider)
        table.add_row("base_url", cfg.base_url)
        table.add_row("model", cfg.model)
        table.add_row("api_token", str(0 != len(cfg.api_token)))
        table.add_row(
            "temperature",
            (
                str(cfg.temperature)
                if cfg.temperature is not None
                else "(default)"
            ),
        )
        table.add_row(
            "max_tokens",
            (
                str(cfg.max_tokens)
                if cfg.max_tokens is not None
                else "(default)"
            ),
        )

        console.print(table)

        console.print("\n[bold cyan]Querying LLM...[/bold cyan]")

        client = ChatClientFactory.create(cfg)
        response = client.query()

        console.print("\n[bold cyan]Response:[/bold cyan]")
        try:
            console.print(JSON(response, indent=2))
        except Exception:  # pylint: disable=W0718  # type:ignore
            data = response
            console.print(Markdown(data))

    def invoke(self) -> None:
        """Main entry point for this class."""

        # Set the effective log level.
        from .args import Args  # pylint: disable=C0415

        log_level = Args.get_effective_log_level_name(self._args)
        import logging  # pylint: disable=C0415

        # Ignore the error message that follows:
        # `logging.getLogger()` exists.
        for handler in logging.getLogger().handlers:
            handler.setLevel(log_level)

        # Print program information.
        log.debug(self._parser.description)
        print(self._parser.description)
        log.debug(self._parser.epilog)
        print(self._parser.epilog)

        if self._args.command == "query":

            config = ChatConfig.from_args_and_env(self._args)
            self.on_query(config)
            return

        config = ChatConfig.from_args_and_env(self._args)
        self.on_query(config)
