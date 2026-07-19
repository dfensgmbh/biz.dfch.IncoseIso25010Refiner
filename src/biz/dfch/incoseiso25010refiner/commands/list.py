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

"""'list' command."""

from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

from ..console import RichUtils
from ..info import Info
from ..session import Session
from .args import WorkspaceOpt

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command("list")
def list_(
    ctx: typer.Context,
    workspace: WorkspaceOpt = Path("."),
):
    """
    Show all sessions path in workspace.
    """

    _ = ctx

    paths = Session.all(workspace)

    sessions = {}
    for path in paths:
        is_valid = Session.is_valid(workspace, path.name)
        value = f"{RichUtils.make_link(path.resolve())} [{is_valid}]"
        sessions[path.name] = value

    console = Console()
    table = RichUtils.make_table(sessions, "Sessions")
    console.print(table)
