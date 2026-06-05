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

"""'restore' command."""

from pathlib import Path
import uuid

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm
import typer

from biz.dfch.logging import log

from ..console import RichUtils
from ..info import Info
from ..session import Session

from .args import WorkspaceOpt
from .args import SessionIdOpt
from .args import YesOpt

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command()
def restore(
    session_id: SessionIdOpt = str(uuid.uuid4()),
    workspace: WorkspaceOpt = Path("."),
    do_not_confirm: YesOpt = False,
):
    """
    Restores the previous version of the source document.
    """

    assert isinstance(workspace, Path), type(workspace)
    path = Path(workspace / session_id).resolve()
    assert path.exists(), f"Path does not exist: '{path}'."
    assert path.is_dir(), f"Path is not a directory: '{path}'."

    session = Session(workspace, session_id)

    table = RichUtils.make_table(
        {
            "workspace": {RichUtils.make_link(workspace)},
            "session_id": RichUtils.make_link(session.path, session_id),
        },
        title="Parameters",
    )

    console = Console()
    console.print(table)

    files = session.source.get_versions()
    if 0 == len(files):
        log.error("No file to restore.")
        return

    file_links = []
    for file in files:
        file_links.append(RichUtils.make_link(file.resolve()))
    log.info(f"Previous versions:\n{'\n'.join(file_links)}")

    file = files[0]
    message = "Do you want to restore file: " f"'{RichUtils.make_link(file)}'?"
    if not do_not_confirm and not Confirm.ask(
        message, show_default=True, default=True
    ):
        log.error("Stop restore.")
        return

    session.source.restore_previous_version()

    log.info(
        "You can now continue your work in: "
        f"'{RichUtils.make_link(session.source.file)}'."
    )
