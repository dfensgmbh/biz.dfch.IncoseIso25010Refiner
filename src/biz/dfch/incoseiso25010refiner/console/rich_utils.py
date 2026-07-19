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

"""
Support functions for `rich`.
"""

from pathlib import Path
from typing import Any

from rich import box
from rich.console import Console
from rich.progress_bar import ProgressBar
from rich.table import Table

from ..parse import Question, SentenceAnalysis


class RichUtils:
    """RichUtils"""

    @staticmethod
    def make_link(path: Path, display: Any | None = None) -> str:
        """
        Make a rich link from a `Path`.

        Args:
            path (Path): The `Path` to make the link from.
            display (Any | None): If specified, this is the "display string" of
                the link.

                If not specified, the link shows the full `path .

                *default*: `None`
        Returns:
            result (str): The `rich` string that contains a link to `path`.
        """

        assert isinstance(path, (Path, str)), type(path)

        if display is None:
            display = path

        if isinstance(path, Path):
            result = f"[link=file://{path}]{str(display)}[/link]"
        else:
            result = f"[link={path}]{str(display)}[/link]"

        return result

    @staticmethod
    def print(value: str) -> None:
        """print_info"""
        Console().print(f"[bold cyan]{value}[/bold cyan]")

    @staticmethod
    def info(value: str) -> None:
        """print_info"""
        Console().print(f"[dim white]{value}[/dim white]")

    @staticmethod
    def error(value: str) -> None:
        """print_info"""
        Console().print(f"[red]{value}[/red]")

    @staticmethod
    def make_table(data: dict, title: str | None = None) -> Table:
        """make_table"""

        if title is None:
            table = Table()
        else:
            assert isinstance(title, str), type(title)
            table = Table(
                title=title,
                header_style="bold cyan",
                show_header=True,
            )

        table.add_column("Parameter", style="cyan")
        # table.add_column("Value", style="green")
        table.add_column("Value")

        for key, value in data.items():
            if isinstance(value, list):
                v = "\n".join(list(value))
            else:
                v = value
            table.add_row(str(key), str(v))

        return table

    @staticmethod
    def create_analysis_table(analysis: list[SentenceAnalysis]) -> Table:
        """create_analysis_table"""
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
    def create_questions_table(questions: list[Question]) -> Table:
        """create_questions_table"""
        table = Table(
            title="ISO 25010 Questions",
            box=box.ROUNDED,
            show_header=False,
            expand=True,
        )

        table.add_column("Content", ratio=1)

        for i, question in enumerate(questions):
            table.add_row(
                f"[bold yellow]{question.characteristic}:[/bold yellow] "
                f"[dim]{question.rationale}[/dim]"
            )
            table.add_row(f"[white]{question.question}[/white]")

            if i < len(questions) - 1:
                table.add_section()  # adds a divider between question groups

        return table

    @staticmethod
    def create_scores_table(scores: list, rationale: str = "") -> Table:
        """create_scores_table"""

        table = Table(
            title="Characteristic Scores",
            box=None,
            show_header=True,
            header_style="bold cyan",
            expand=True,
        )

        table.add_column("Characteristic", style="bold yellow", min_width=20)
        table.add_column("Rationale", style="white", ratio=1)

        if isinstance(rationale, str) and rationale.strip():
            table.add_row(
                "General",
                rationale,
            )

        for score in scores:
            table.add_row(
                # str(score.score),
                score.characteristic,
                score.rationale,
            )

        return table

    @staticmethod
    def _bar_style(score: float) -> str:
        if score >= 0.7:  # noqa: PLR2004
            return "green"

        if score >= 0.5:  # noqa: PLR2004
            return "yellow"

        return "red"

    @staticmethod
    def create_iso25010_chart(scores: list) -> Table:
        """Display ISO 25010 scores as a horizontal bar chart."""
        table = Table(
            title="ISO/IEC 25010 Quality Characteristics Coverage",
            box=None,
            header_style="bold cyan",
            show_header=True,
        )
        table.add_column("Characteristic", style="bold yellow", width=28)
        table.add_column("Score", width=40)
        table.add_column("Value", justify="right", width=6)

        for score in scores:
            progress_bar = ProgressBar(
                total=1.0,
                completed=score.score,
                width=40,
                style="grey35",
                complete_style=RichUtils._bar_style(score.score),
            )
            table.add_row(
                score.characteristic, progress_bar, f"{score.score:.2f}"
            )

        return table
