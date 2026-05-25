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

"""'stub' command."""

from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm
import typer

from biz.dfch.diagnostics import Clock
from biz.dfch.logging import log

from ..session import Session

from ..constant import Constant
from ..info import Info
from ..iso25010 import Iso25010
from ..parse import parse_iso_response
from ..text.file_utils import FileUtils
from ..ui.rich_utils import RichUtils

from .args import FileOpt
from .args import CharacteristicsOpt
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
def stub(
    ctx: typer.Context,
    session_id: SessionIdOpt,
    workspace: WorkspaceOpt = Path("."),
    # file: FileOpt = None,  # type: ignore
    characteristics: CharacteristicsOpt = None,
):
    """
    This commands is a stub and a test-bed for future testing.
    """

    if characteristics is None:
        characteristics = Iso25010.all()

    session = Session.create(
        workspace, session_id, characteristics, "Lorem ipsum dolor sit amet."
    )

    log.fatal("source: '%s'.", session.source.file)

    return

    # p = ctx.obj["print"]
    # p.debug("tralala print error")
    # p.info("tralala print info")
    # p.warning("tralala print warn")
    # p.error("tralala print error")
    # p.fatal("tralala print fatal")

    # p.table({"name1": "value"})
    console = Console()

    # log.debug("Schnittenfittich log debug")
    # log.info("Schnittenfittich log info")
    # log.warning("Schnittenfittich log warning")
    # log.error("Schnittenfittich log error")
    # log.fatal("Schnittenfittich log fatal")

    # console.print(f"ctx: '{type(ctx)}")
    # raise typer.BadParameter("Tralala.")
    raise typer.Exit(0)

    assert isinstance(workspace, Path), type(workspace)
    path = Path(workspace / session_id).resolve()
    assert path.exists(), f"Path does not exist: '{path}'."

    source_doc = path / Constant.SOURCE_DOCUMENT
    assert source_doc.exists(), f"File does not exist: '{source_doc}'."
    assert source_doc.is_file(), f"File is not a file: '{source_doc}'."

    text = session.source.contents

    if file is not None:
        full_name = Path(path / file).resolve()
        assert full_name.exists(), f"File does not exist: '{full_name}'."
        assert full_name.is_file(), f"File is not a file: '{full_name}'."
        files = [full_name]
    else:
        pattern = (
            f"{Constant.RESPONSE_FILE_PREFIX}*{Constant.RESPONSE_FILE_EXT}"
        )
        files = sorted(path.glob(pattern), reverse=True)

    if characteristics is None:
        characteristics = Iso25010.all()

    data = {
        "workspace": str(workspace),
        "session_id": session_id,
        "characteristics": characteristics,
        "file": file,
    }
    log.debug("Parameters: [%s]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console.print(table)

    for f in files:
        result = Confirm.ask(
            f"Do you want to commit the questions from file '{f}'?",
            show_default=True,
            default=False,
        )
        if not result:
            continue

        # Parse response.
        text = f.read_text(encoding="utf-8")
        iso25010_response = parse_iso_response(text)

        # Create copy of source document.
        timestamp = Clock.now_file()
        RichUtils.print("Making copy of source document ...")
        source_copy = FileUtils.make_copy(source_doc, f"---{timestamp}")
        assert source_copy.exists(), source_copy
        RichUtils.info(f"Making copy of source document '{source_copy}' OK.")

        # Change source document and add new questions to it.
        updated = FileUtils.update_source_doc(
            source_doc, iso25010_response.questions
        )
        source_doc.write_text(updated, encoding="utf-8")

        console.print(
            f"You can now continue your work in: '[link=file:///{source_doc}]"
            f"{source_doc}[/link]'."
        )

        break
