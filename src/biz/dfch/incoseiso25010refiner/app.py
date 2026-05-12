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
from datetime import datetime
import json
from pathlib import Path
import re

from rich.console import Console
from rich.json import JSON
from rich.markdown import Markdown
from rich.progress_bar import ProgressBar
from rich.table import Table
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

    @staticmethod
    def _remove_md_json(response: str) -> str:
        """Removes markdown JSON formatting from specified text."""

        # Use regex to find content between ```json and ``` or just ``` and ```
        # The [^`]*? is a non-greedy match for everything that isn't a backtick
        pattern = r"```(?:json)?\s*(.*?)\s*```"
        match = re.search(pattern, response, re.DOTALL)

        if match:
            result = match.group(1).strip()
        else:
            # Fallback: model might have returned naked JSON or failed the block
            result = response.strip()

        return result

    @staticmethod
    def _is_json(text: str) -> bool:
        """Examine if the given text is valid JSON."""
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
            return False

    @staticmethod
    def _make_config_table(cfg: ChatConfig) -> Table:

        assert isinstance(cfg, ChatConfig)

        table = Table(
            title="Configuration",
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("Setting", style="bold")
        table.add_column("Value")

        table.add_row("prompt", Markdown(cfg.prompt))
        table.add_row("template", cfg.template)
        table.add_row(
            "request_size", str(len(cfg.prompt) + len(cfg.template_content))
        )
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

        return table

    def on_init(self, cfg: ChatConfig) -> None:
        """This method processes the `init` argument."""

        assert isinstance(cfg, ChatConfig)

        console = Console()
        table = App._make_config_table(cfg)
        console.print(table)

        console.print("\n[bold cyan]Querying LLM...[/bold cyan]")

        client = ChatClientFactory.create(cfg)
        response = client.query()

        timestamp = datetime.now().strftime("%Y-%m-%d---%H-%M-%S")
        text = App._remove_md_json(response)
        is_json = App._is_json(text)

        console.print("\n[bold cyan]Response:[/bold cyan]")
        try:
            console.print(JSON(text, indent=2))
        except Exception:  # pylint: disable=W0718  # type:ignore
            console.print(Markdown(text))

        assert is_json
        extension = ".json"
        file_path = Path(cfg.output_path) / f"{cfg.session_id}{extension}"
        file_path.write_text(text, encoding="utf-8")
        file_path = (
            Path(cfg.output_path) / f"{cfg.session_id}---{timestamp}{extension}"
        )
        file_path.write_text(text, encoding="utf-8")

        from .parse import IsoResponse, parse_iso_response

        iso25010_response = parse_iso_response(text)
        for score in iso25010_response.summary.scores:
            print(f"{score.characteristic} [{score.score}]: {score.rationale}")

        App.display_iso25010_chart(iso25010_response.summary.scores, console)

    @staticmethod
    def _bar_style(score: float) -> str:
        if score >= 0.7:
            return "green"

        if score >= 0.5:
            return "yellow"

        return "red"

    @staticmethod
    def display_iso25010_chart(scores: list, console: Console) -> None:
        """Display ISO 25010 scores as a horizontal bar chart."""
        table = Table(
            title="ISO/IEC 25010 Quality Characteristics",
            box=None,
            show_header=True,
        )
        table.add_column("Characteristic", style="cyan", width=28)
        table.add_column("Score", width=40)
        table.add_column("Value", justify="right", width=6)

        for score in scores:
            progress_bar = ProgressBar(
                total=1.0,
                completed=score.score,
                width=40,
                style="grey35",
                complete_style=App._bar_style(score.score),
            )
            table.add_row(
                score.characteristic, progress_bar, f"{score.score:.2f}"
            )

        console.print(table)

    def on_query(self, cfg: ChatConfig) -> None:
        """This method processes the `query` argument."""

        assert isinstance(cfg, ChatConfig)

        console = Console()
        table = App._make_config_table(cfg)
        console.print(table)

        console.print("\n[bold cyan]Querying LLM...[/bold cyan]")

        client = ChatClientFactory.create(cfg)
        response = client.query()

        timestamp = datetime.now().strftime("%Y-%m-%d---%H-%M-%S")
        text = App._remove_md_json(response)
        extension = ".json" if App._is_json(text) else ".md"
        file_path = Path(cfg.output_path) / f"{cfg.session_id}{extension}"
        file_path.write_text(text, encoding="utf-8")
        file_path = (
            Path(cfg.output_path) / f"{cfg.session_id}---{timestamp}{extension}"
        )
        file_path.write_text(text, encoding="utf-8")

        console.print("\n[bold cyan]Response:[/bold cyan]")
        try:
            console.print(JSON(text, indent=2))
        except Exception:  # pylint: disable=W0718  # type:ignore
            console.print(Markdown(text))

    def invoke(self) -> None:
        """Main entry point for this class."""

        # Set the effective log level.
        from .args import Args  # pylint: disable=C0415

        log_level = Args.get_effective_log_level_name(self._args)
        import logging  # pylint: disable=C0415

        # Ignore the error message that follows:
        # `logging.getLogger()` does exist.
        for handler in logging.getLogger().handlers:  # type: ignore[attr-defined]  # pylint: disable=E1101  # noqa: E501
            handler.setLevel(log_level)

        # Print program information.
        log.debug(self._parser.description)
        print(self._parser.description)
        log.debug(self._parser.epilog)
        print(self._parser.epilog)

        if self._args.command == "init":

            config = ChatConfig.from_args_and_env(self._args)
            self.on_init(config)
            return

        if self._args.command == "query":

            config = ChatConfig.from_args_and_env(self._args)
            self.on_query(config)
            return

        config = ChatConfig.from_args_and_env(self._args)
        self.on_query(config)
