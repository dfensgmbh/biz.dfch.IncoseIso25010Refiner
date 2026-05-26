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

"""'show' command."""

from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
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
def show(
    session_id: SessionIdOpt,
    workspace: WorkspaceOpt = Path("."),
):
    """
    Show the contents of the source document.
    """

    assert isinstance(workspace, Path), type(workspace)
    path = Path(workspace / session_id).resolve()
    assert path.exists(), f"Path does not exist: '{path}'."

    session = Session(workspace, session_id)

    data = {
        "workspace": f"[link=file://{workspace}]{workspace}[/link]",
        "session_id": f"[link=file://{session.path}]{session_id}[/link]",
    }
    log.debug("Parameters: [%s]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console = Console()
    console.print(table)

    console.print(Markdown(session.source.contents))
