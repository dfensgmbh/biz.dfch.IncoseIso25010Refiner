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

"""'init' command."""

from pathlib import Path
import uuid

from dotenv import load_dotenv
from rich.console import Console
import typer

from ..info import Info
from ..iso25010 import Iso25010
from ..session import Session
from ..ui.rich_utils import RichUtils

from .args import WorkspaceOpt
from .args import SessionIdOpt
from .args import CharacteristicsOpt
from .args import InputOpt

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command()
def init(
    text: InputOpt,
    session_id: SessionIdOpt = str(uuid.uuid4()),
    workspace: WorkspaceOpt = Path("."),
    characteristics: CharacteristicsOpt = None,
):
    """
    Initialise the workspace and source document.

    This command sets up the local environment and ensures the
    specified workspace path is valid for the upcoming session.
    """

    assert isinstance(workspace, Path), type(workspace)
    path = Path(workspace / session_id).resolve()
    assert not path.exists(), f"Path must not exist: '{path}'."
    assert text.strip()

    input_file = Path(text)
    if input_file.exists() and input_file.is_file():
        text = input_file.read_text(encoding="utf-8")

    if characteristics is None:
        characteristics = Iso25010.all()

    table = RichUtils.make_table(
        {
            "workspace": RichUtils.make_link(workspace),
            "session_id": RichUtils.make_link(path, session_id),
            "characteristics": characteristics,
            "input": text,
        },
        title="Parameters",
    )

    console = Console()
    console.print(table)

    session = Session.create(
        workspace, name=session_id, characteristics=characteristics, title=text
    )

    console.print(
        "You can now start your work in: "
        f"'{RichUtils.make_link(session.source.file)}'."
    )
