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

"""'diff' command."""

from difflib import unified_diff
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.syntax import Syntax
import typer

from biz.dfch.logging import log

from ..info import Info
from ..session import Session
from ..ui.rich_utils import RichUtils

from .args import SessionIdOpt
from .args import WorkspaceOpt

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command()
def diff(
    session_id: SessionIdOpt,
    workspace: WorkspaceOpt = Path("."),
):
    """
    Show difference between the current and the previous version of the source
    document.
    """

    assert isinstance(workspace, Path), type(workspace)
    path = Path(workspace / session_id).resolve()
    assert path.exists(), f"Path does not exist: '{path}'."

    session = Session(workspace, session_id)

    source = session.source
    src = {
        "file": session.source.file,
        "name": session.source.file.name,
    }

    previous = session.source.get_previous_version()
    prv = {
        "file": Path("."),
        "name": "None",
    }
    prv_lines: list[str] = []
    if previous is not None:
        prv_lines = previous.lines
        prv["file"] = previous.file
        prv["name"] = previous.file.name

    data = {
        "workspace": RichUtils.make_link(workspace),
        "session_id": RichUtils.make_link(session.path, session_id),
        "source": RichUtils.make_link(Path(str(src['file'])), src['name']),
        "previous": RichUtils.make_link(Path(str(prv['file'])), prv['name']),
    }
    log.debug("Parameters: [%s]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console = Console()
    console.print(table)

    diff_lines = unified_diff(
        prv_lines,
        source.lines,
        fromfile=str(prv["name"]),
        tofile=str(src["name"]),
        lineterm="",
    )
    diff_text = "\n".join(diff_lines)

    if not diff_text:
        console.print("[dim]No changes.[/dim]")
        return

    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    console.print(syntax)
