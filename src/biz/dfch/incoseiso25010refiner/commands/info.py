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

"""'info' command."""

from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
import typer

from biz.dfch.logging import log

from ..info import Info
from ..session import Session
from ..console import RichUtils

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
def info(
    session_id: SessionIdOpt,
    workspace: WorkspaceOpt = Path("."),
):
    """
    Show information about the specified the session.
    """

    assert isinstance(workspace, Path), type(workspace)
    path = Path(workspace / session_id).resolve()
    assert path.exists(), f"Path does not exist: '{path}'."

    session = Session(workspace, session_id)

    def get_links(items: list[Path]) -> list[str]:
        assert isinstance(items, list), type(items)

        return [
            RichUtils.make_link(i.resolve(), i.resolve().name) for i in items
        ]

    source_stem = session.source.file.stem
    data = {
        "workspace": RichUtils.make_link(workspace),
        "session_id": RichUtils.make_link(session.path, session_id),
        "source": RichUtils.make_link(session.source.file),
        "versions": "\n".join(get_links(session.source.get_versions())),
        "items": "\n".join(
            get_links(
                [
                    i
                    for i in session.get_items()
                    if not i.stem.startswith(source_stem)
                ]
            )
        ),
    }
    log.debug("Parameters: [%s]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console = Console()
    console.print(table)
