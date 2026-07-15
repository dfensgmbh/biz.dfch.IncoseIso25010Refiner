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

"""Program entry point with typer."""

# pylint: disable=C0413
# flake8: noqa: E402

from dotenv import load_dotenv
import typer

from biz.dfch.i18n import I18n

I18n.Factory.create("biz/dfch/incoseiso25010refiner")

from biz.dfch.incoseiso25010refiner.commands import checkpoint
from biz.dfch.incoseiso25010refiner.commands import replay
from biz.dfch.incoseiso25010refiner.commands import diff
from biz.dfch.incoseiso25010refiner.commands import ui
from biz.dfch.incoseiso25010refiner.commands import info
from biz.dfch.incoseiso25010refiner.commands import init
from biz.dfch.incoseiso25010refiner.commands import jira
from biz.dfch.incoseiso25010refiner.commands import erase
from biz.dfch.incoseiso25010refiner.commands import list_
from biz.dfch.incoseiso25010refiner.commands import query
from biz.dfch.incoseiso25010refiner.commands import refine
from biz.dfch.incoseiso25010refiner.commands import resolve
from biz.dfch.incoseiso25010refiner.commands import restore
from biz.dfch.incoseiso25010refiner.commands import show
from biz.dfch.incoseiso25010refiner.commands import stage
from biz.dfch.incoseiso25010refiner.commands import stub
from biz.dfch.incoseiso25010refiner.commands import summary
from biz.dfch.incoseiso25010refiner.commands import translate
from biz.dfch.incoseiso25010refiner.commands import validate
from biz.dfch.incoseiso25010refiner.commands import vector

from biz.dfch.incoseiso25010refiner.info import Info

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.callback()
def _callback(ctx: typer.Context):
    # We use `callback` only to make sure that `typer` continues to show
    # "sub-commands" when there is only one "sub-command".

    _ = ctx

    return


app.command(name="list", epilog=Info.epilog)(list_)
app.command(epilog=Info.epilog)(checkpoint)
app.command(epilog=Info.epilog)(replay)
app.command(epilog=Info.epilog)(diff)
app.command(epilog=Info.epilog)(erase)
app.command(epilog=Info.epilog)(ui)
app.command(epilog=Info.epilog)(info)
app.command(epilog=Info.epilog)(init)
app.command(epilog=Info.epilog)(jira)
app.command(epilog=Info.epilog)(query)
app.command(epilog=Info.epilog)(refine)
app.command(epilog=Info.epilog)(resolve)
app.command(epilog=Info.epilog)(restore)
app.command(epilog=Info.epilog)(show)
app.command(epilog=Info.epilog)(stage)
app.command(epilog=Info.epilog)(stub)
app.command(epilog=Info.epilog)(summary)
app.command(epilog=Info.epilog)(translate)
app.command(epilog=Info.epilog)(validate)
app.command(epilog=Info.epilog)(vector)

if __name__ == "__main__":
    app()
