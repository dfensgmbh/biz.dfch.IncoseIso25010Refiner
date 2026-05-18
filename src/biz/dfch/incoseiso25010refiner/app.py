# Copyright (C) 2026 Ronald Rink, d-fens GmbH, http://d-fens.ch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Main app module."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import time

from rich.console import Console
from rich.json import JSON
from rich.markdown import Markdown
from rich.table import Table
from rich.theme import Theme

from biz.dfch.logging import log
from biz.dfch.version import Version

from .chat.chat_config import ChatConfig
from .chat.chat_client_factory import ChatClientFactory
from .parse import (
    parse_iso_response,
    Question,
)

from .ui.rich_utils import RichUtils
from .text.text_utils import TextUtils
from .text.file_utils import FileUtils
from .iso25010 import Iso25010


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

    def on_validate(self, file: str) -> None:
        """This method processes the `validate` argument."""

        # assert isinstance(file, Path), type(file)
        assert isinstance(file, str), type(file)

        # text = file.read_text(encoding="utf8")
        text = file

        is_json = TextUtils.is_json(text)
        console = Console()
        console.print(is_json)

        _ = json.loads(text)

    def on_init(self, cfg: ChatConfig) -> None:
        """This method processes the `init` argument."""

        assert isinstance(cfg, ChatConfig)

        console = Console()
        table = App._make_config_table(cfg)
        console.print(table)

        start_time = datetime.now().strftime("%Y-%m-%d---%H-%M-%S")
        console.print(
            f"\n[bold cyan]{start_time}: Querying LLM ...[/bold cyan]"
        )
        client = ChatClientFactory.create(cfg)

        timestamp = time.perf_counter()
        try:
            response = client.query()
        except TimeoutError:
            elapsed = time.perf_counter() - timestamp
            console.print(
                f"\n[dim red]{start_time}: Querying LLM FAIL. TotalSeconds: "
                f"{elapsed:.3f}.[/dim red]"
            )
            raise

        stop_time = datetime.now().strftime("%Y-%m-%d---%H-%M-%S")
        elapsed = time.perf_counter() - timestamp
        console.print(
            f"\n[dim white]{stop_time}: Querying LLM OK. TotalSeconds: "
            f"{elapsed:.3f}.[/dim white]"
        )

        start_time = datetime.now().strftime("%Y-%m-%d---%H-%M-%S")
        text = TextUtils.remove_md_json(response)
        text = TextUtils.clean_pseudo_json(text)
        is_json = TextUtils.is_json(text)
        if not is_json:
            text = TextUtils.clean_text(text)
        is_json = TextUtils.is_json(text)

        console.print("\n[bold cyan]Response:[/bold cyan]")
        try:
            console.print(JSON(text, indent=2))
        except Exception:  # pylint: disable=W0718  # type:ignore
            console.print(Markdown(text))

        extension = ".json" if is_json else ".txt"
        backup_file_path = (
            Path(cfg.output_path)
            / f"{cfg.session_id}---{start_time}{extension}"
        )
        backup_file_path.write_text(text, encoding="utf-8")

        assert is_json, "Try operation one more time."
        iso25010_response = parse_iso_response(text)

        # for question in iso25010_response.questions:
        #     characteristic: str
        #     rationale: str
        #     question: str

        result = RichUtils.create_analysis_table(iso25010_response.analysis)
        console.print(result)

        result = RichUtils.create_questions_table(iso25010_response.questions)
        console.print(result)

        extension = ".md"
        session_file_path = (
            Path(cfg.output_path) / f"{cfg.session_id}{extension}"
        )
        if not session_file_path.exists():
            text = f"""// This is the initial draft for the requirement set '{cfg.session_id}'.
// Title: '<TITLE OF REQUIREMENT SET>'

# General

{cfg.prompt}

# {Iso25010.FUNCTIONALITY}

# {Iso25010.PERFORMANCE}

# {Iso25010.COMPATIBILITY}

# {Iso25010.INTERACTION}

# {Iso25010.RELIABILITY}

# {Iso25010.SECURITY}

# {Iso25010.MAINTAINABILITY}

# {Iso25010.FLEXIBILITY}

# {Iso25010.SAFETY}


"""
            session_file_path.write_text(text, encoding="utf-8")

        updated = FileUtils.update_source_doc(
            session_file_path, iso25010_response.questions
        )
        session_file_path.write_text(updated, encoding="utf-8")

        result = RichUtils.create_scores_table(iso25010_response.summary.scores)
        console.print(result)

        result = RichUtils.create_iso25010_chart(
            iso25010_response.summary.scores
        )
        console.print(result)

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
        text = TextUtils.remove_md_json(response)
        extension = ".json" if TextUtils.is_json(text) else ".md"
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

        if self._args.command == "validate":

            json_text = getattr(self._args, "json", None)
            assert json_text is not None
            # file = Path(json_text)

            self.on_validate(json_text)
            return

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
