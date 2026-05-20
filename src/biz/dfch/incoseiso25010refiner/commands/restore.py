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

from ..constant import Constant
from ..ui.rich_utils import RichUtils
from ..info import Info

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
    Restores the last copy of the source document.
    """

    assert isinstance(workspace, Path), type(workspace)
    path = Path(workspace / session_id).resolve()
    assert path.exists(), f"Path does not exist: '{path}'."
    assert path.is_dir(), f"Path is not a directory: '{path}'."

    table = RichUtils.make_table(
        {
            "workspace": workspace,
            "session_id": session_id,
        },
        title="Parameters",
    )

    console = Console()
    console.print(table)

    source_doc = Path(path) / Constant.SOURCE_DOCUMENT
    assert source_doc.exists(), f"File does not exist: '{source_doc}'."
    assert source_doc.is_file(), f"File is not a file: '{source_doc}'."

    pattern = f"{source_doc.stem}---*{source_doc.suffix}"
    files = sorted(source_doc.parent.glob(pattern), reverse=True)
    if 0 == len(files):
        RichUtils.error("No file to restore.")
        return

    file_links = []
    for file in files:
        file_links.append(
            f"[link=file:///{file.resolve()}]{file.resolve()}[/link]"
        )
    RichUtils.info(f"Versions:\n{'\n'.join(file_links)}")

    file = files[0]
    message = (
        f"Do you want to restore file: '[link=file:///{file}]{file}[/link]'?"
    )
    if not do_not_confirm and not Confirm.ask(message):
        RichUtils.error("Stop restore.")
        return

    RichUtils.print(f"Restore file: '[link=file:///{file}]{file}[/link]' ...")
    # Delete file.
    source_doc.unlink()
    # Rename copy to source file.
    file.rename(str(source_doc))

    console.print(
        f"You can now continue your work in: '[link=file:///{source_doc}]"
        f"{source_doc}[/link]'."
    )
