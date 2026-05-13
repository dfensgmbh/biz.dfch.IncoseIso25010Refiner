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

from rich import box
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
from .parse import (
    parse_iso_response,
    ScoreSummary,
    SentenceAnalysis,
    Question,
    Summary,
)

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

        extension = ".json" if is_json else ".txt"
        backup_file_path = (
            Path(cfg.output_path) / f"{cfg.session_id}---{timestamp}{extension}"
        )
        backup_file_path.write_text(text, encoding="utf-8")

        assert is_json, "Try operation one more time."
        iso25010_response = parse_iso_response(text)

        # for question in iso25010_response.questions:
        #     characteristic: str
        #     rationale: str
        #     question: str

        result = App._create_analysis_table(iso25010_response.analysis)
        console.print(result)

        result = App._create_questions_table(iso25010_response.questions)
        console.print(result)

        extension = ".md"
        session_file_path = (
            Path(cfg.output_path) / f"{cfg.session_id}{extension}"
        )
        if not session_file_path.exists():
            text = f"""// This is the initial draft for the requirement set '{cfg.session_id}'.
// Title: '<TITLE OF REQUIREMENT SET>'

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

        updated = App._update_file(
            session_file_path, iso25010_response.questions
        )
        session_file_path.write_text(updated, encoding="utf-8")

        result = App._create_scores_table(iso25010_response.summary.scores)
        console.print(result)

        result = App._create_iso25010_chart(iso25010_response.summary.scores)
        console.print(result)

    @staticmethod
    def _update_file(file: Path, questions: list[Question]) -> str:
        assert isinstance(file, Path), type(file)
        assert file.exists(), file
        assert file.is_file(), file
        assert isinstance(questions, list), type(questions)

        lines = file.read_text(encoding="utf-8").splitlines()

        # Move from end to start.
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]

            for characteristic in Iso25010:
                if line.startswith(f"# {characteristic}"):
                    new_lines = [""]
                    for q in [
                        q.question
                        for q in questions
                        if q.characteristic == characteristic
                    ]:
                        new_lines.append(f"// {characteristic}")
                        new_lines.append(f"> {q}")
                        new_lines.append("")

                    for j, new_line in enumerate(new_lines):
                        lines.insert(i + 1 + j, new_line)
                    break

        lines.append("")
        result: str = "\n".join(lines)

        return result

    @staticmethod
    def _create_analysis_table(analysis: list[SentenceAnalysis]) -> Table:
        table = Table(
            title="Sentence Analysis",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
            expand=True,
        )

        table.add_column("#", style="bold white", justify="center", min_width=4)
        table.add_column(
            "Id", style="bold white", justify="center", min_width=4
        )
        table.add_column("Classifications", style="bold yellow", min_width=22)
        table.add_column("Text", style="white", ratio=1)

        for item in analysis:
            table.add_row(
                str(item.line_number),
                str(item.sentence_id),
                "\n".join([c.characteristic for c in item.classifications]),
                item.sentence,
            )
            table.add_section()

        return table

    @staticmethod
    def _create_questions_table(questions: list[Question]) -> Table:
        table = Table(
            title="ISO 25010 Questions",
            box=box.ROUNDED,
            show_header=False,
            expand=True,
        )

        table.add_column("Content", ratio=1)

        for i, question in enumerate(questions):
            table.add_row(
                f"[bold yellow]{question.characteristic}:[/bold yellow] [dim]{question.rationale}[/dim]"
            )
            table.add_row(f"[white]{question.question}[/white]")

            if i < len(questions) - 1:
                table.add_section()  # adds a divider between question groups

        return table

    @staticmethod
    def _create_scores_table(scores: list) -> Table:

        table = Table(
            title="Characteristic Scores",
            box=None,
            show_header=True,
            header_style="bold cyan",
            expand=True,
        )

        # table.add_column(
        #     "Score", style="bold yellow", justify="center", min_width=8
        # )
        table.add_column("Characteristic", style="bold cyan", min_width=20)
        table.add_column("Rationale", style="white", ratio=1)

        for score in scores:
            table.add_row(
                # str(score.score),
                score.characteristic,
                score.rationale,
            )

        return table

    @staticmethod
    def _bar_style(score: float) -> str:
        if score >= 0.7:
            return "green"

        if score >= 0.5:
            return "yellow"

        return "red"

    @staticmethod
    def _create_iso25010_chart(scores: list) -> Table:
        """Display ISO 25010 scores as a horizontal bar chart."""
        table = Table(
            title="ISO/IEC 25010 Quality Characteristics Coverage",
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

        return table

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
