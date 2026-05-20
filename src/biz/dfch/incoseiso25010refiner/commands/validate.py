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

"""'validate' command."""

import json

import typer
from dotenv import load_dotenv

from biz.dfch.logging import log

from ..info import Info
from ..text.text_utils import TextUtils

from .args import FileOpt

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command()
def validate(
    file: FileOpt,
):
    """
    Examine if the specified file is valid JSON.
    """

    text = file.read_text(encoding="utf-8")

    is_json = TextUtils.is_json(text)
    if is_json:
        log.debug("'%s' [is_json: %s]", file, is_json)
    else:
        log.error("'%s' [is_json: %s]", file, is_json)

    _ = json.loads(text)
