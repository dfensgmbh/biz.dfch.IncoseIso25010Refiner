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

import typer

from biz.dfch.i18n import I18n

I18n.Factory.create("biz/dfch/incoseiso25010refiner")

from biz.dfch.incoseiso25010refiner.commands import init
from biz.dfch.incoseiso25010refiner.commands import query
from biz.dfch.incoseiso25010refiner.commands import refine
from biz.dfch.incoseiso25010refiner.commands import validate

from biz.dfch.incoseiso25010refiner.info import Info

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.callback()
def _callback():
    # We use `callback` only to make sure that `typer` continues to show
    # "sub-commands" when there is only one "sub-command".
    pass


app.command(epilog=Info.epilog)(init)
app.command(epilog=Info.epilog)(query)
app.command(epilog=Info.epilog)(refine)
app.command(epilog=Info.epilog)(validate)

if __name__ == "__main__":
    app()
