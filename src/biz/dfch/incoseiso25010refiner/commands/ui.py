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

"""'gui' command."""

from pathlib import Path

import typer
from dotenv import load_dotenv

from biz.dfch.i18n import LanguageCode
from biz.dfch.logging import log

from ..info import Info
from ..tui import Tui
from .args import LanguageOpt, SessionIdOpt, WorkspaceOpt

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command()
def ui(
    session_id: SessionIdOpt,
    workspace: WorkspaceOpt = Path("."),
    language: LanguageOpt = LanguageCode.EN,
):
    """
    Launch the graphical user interface.
    """

    assert isinstance(workspace, Path), type(workspace)
    path = Path(workspace / session_id).resolve()
    assert path.exists(), f"Path does not exist: '{path}'."

    log.debug(
        "Parameters: (workspace=%s, session_id=%s, language=%s)",
        workspace,
        session_id,
        language,
    )

    tui = Tui(workspace=workspace, session_id=session_id, language=language)
    tui.run()
