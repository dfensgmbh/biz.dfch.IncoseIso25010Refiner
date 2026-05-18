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

"""main program with typer"""

# pylint: disable=C0413
# flake8: noqa: E402

import typer

from biz.dfch.i18n import I18n

I18n.Factory.create("biz/dfch/incoseiso25010refiner")

from biz.dfch.incoseiso25010refiner.commands import init
from biz.dfch.incoseiso25010refiner.commands import refine
from biz.dfch.incoseiso25010refiner.commands import validate

app = typer.Typer(no_args_is_help=True)
@app.callback()
def _callback():
    pass

app.command()(init)
app.command()(refine)
app.command()(validate)

if __name__ == "__main__":
    app()
