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

"""'erase' command."""

from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.prompt import Confirm

from biz.dfch.logging import log

from ..info import Info
from ..session import Session
from .args import SessionIdOpt, WorkspaceOpt, YesOpt

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


def erase(
    ctx: typer.Context,
    session_id: SessionIdOpt,
    workspace: WorkspaceOpt = Path("."),
    do_not_confirm: YesOpt = False,
):
    """
    Erase the specified session from the workspace.
    """

    _ = ctx

    message = f"Do you want to erase the session with id '{session_id}' in '{workspace}'?"
    if not do_not_confirm and not Confirm.ask(message, show_default=True, default=True):
        log.error("Stop erase.")
        return

    log.debug("Erase session id '%s' in '%s' ...", session_id, workspace)
    try:
        Session.erase(workspace, session_id)
        log.info("Erase session id '%s' in '%s' OK.", session_id, workspace)
    except Exception as ex:  # pylint: disable=W0718
        log.error(
            "Erase session id '%s' in '%s' FAILED.",
            session_id,
            workspace,
            exc_info=ex,
        )
