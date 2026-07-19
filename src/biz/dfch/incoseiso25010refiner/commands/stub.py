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

import typer
from dotenv import load_dotenv

from ..info import Info
from ..iso25010 import Iso25010
from .args import CharacteristicsOpt, SessionIdOpt, WorkspaceOpt

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
    characteristics: CharacteristicsOpt = None,
):
    """
    This commands is a stub and a test-bed for future testing.
    """

    assert isinstance(ctx, typer.Context), type(ctx)
    assert isinstance(session_id, str), type(session_id)
    assert isinstance(workspace, Path), type(workspace)

    if characteristics is None:
        characteristics = Iso25010.all()

    raise NotImplementedError()
