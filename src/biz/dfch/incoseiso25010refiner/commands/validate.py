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

    log.debug("Read file: '%s' ...", file.name)
    text = file.read_text(encoding="utf-8")
    log.info("Read file: '%s' OK.", file.name)

    log.debug("Examine if file '%s' is JSON ...", file)
    is_json = TextUtils.is_json(text)
    if is_json:
        log.info("Examine if file '%s' is JSON: %s", file, is_json)
    else:
        log.error("Examine if file '%s' is JSON: %s", file, is_json)

    log.debug("Read file '%s' as JSON ...", file)
    _ = json.loads(text)
    log.info("Read file '%s' as JSON OK.", file)
