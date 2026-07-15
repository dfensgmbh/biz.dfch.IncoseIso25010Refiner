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

# flake8: noqa=E501
# pylint: disable=C0103
# pylint: disable=C0301

"""'stage' command."""

import json
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
import typer

from biz.dfch.logging import log

from ..console import RichUtils
from ..constant import Constant
from ..chat.providers import Providers
from ..info import Info
from ..iso25010 import Iso25010
from ..parse import Requirement
from ..parse import RequirementStatus
from ..parse.models import parse_iso_response
from ..session import Session

from .args import ApiTokenOpt
from .args import BaseUriOpt
from .args import CharacteristicsOpt
from .args import MaxTokensOpt
from .args import ModelOpt
from .args import ProviderOpt
from .args import SessionIdOpt
from .args import TemperateOpt
from .args import WorkspaceOpt

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command()
def stage(
    api_token: ApiTokenOpt,
    session_id: SessionIdOpt,
    uri: BaseUriOpt = "",
    model: ModelOpt = "",
    temperature: TemperateOpt = -1,
    max_tokens: MaxTokensOpt = -1,
    provider: ProviderOpt = Providers.DEFAULT,
    workspace: WorkspaceOpt = Path("."),
    characteristics: CharacteristicsOpt = None,
):
    """Split requirements from the last response JSON into separate JSON requirements."""

    assert isinstance(workspace, Path), type(workspace)
    path = Path(workspace / session_id).resolve()
    assert path.exists(), f"Path must exist: '{path}'."

    if characteristics is None:
        characteristics = Iso25010.all()

    log.debug("Get session '%s' ...", session_id)
    session = Session(workspace, session_id)
    log.info("Get session '%s' OK.", session_id)

    data = {
        "workspace": RichUtils.make_link(workspace),
        "session_id": RichUtils.make_link(session.path, session_id),
        "provider": provider,
        "api_token": 0 < len(api_token),
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "characteristics": characteristics,
    }
    log.debug("Parameters: [%s]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console = Console()
    console.print(table)

    # Load the most recent response file from the session.
    response_base = Constant.RESPONSE_FILE_PREFIX.rstrip("-")
    log.debug("Loading last response item from session '%s' ...", session_id)
    response_items = session.get_items(response_base)
    assert len(response_items) > 0, (
        f"No response files found in session '{session_id}'. "
        "Run the 'refine' command first."
    )
    last_response_file = response_items[0]
    log.info(
        "Loading last response item from session '%s' OK: '%s'.",
        session_id,
        last_response_file,
    )

    response_json = last_response_file.read_text(encoding="utf-8")
    iso_response = parse_iso_response(response_json)

    # Convert each analysis sentence into a Requirement and save as JSON.
    log.debug(
        "Converting %d analysis items to requirements ...",
        len(iso_response.analysis),
    )
    saved: list[Path] = []
    for item in iso_response.analysis:
        # Collect unique ISO 25010 characteristics from all classifications,
        # preserving insertion order.
        seen: set[str] = set()
        chars: list[Iso25010] = []
        for cls in item.classifications:
            if cls.characteristic not in seen:
                seen.add(cls.characteristic)
                chars.append(Iso25010(cls.characteristic))

        # Build a combined rationale from all classifications.
        combined_rationale = " | ".join(
            f"{cls.characteristic}: {cls.rationale}"
            for cls in item.classifications
        )

        req = Requirement(
            name=item.sentence,
            description=item.sentence,
            rationale=combined_rationale,
            consequences="",
            characteristics=chars,
            status=RequirementStatus.PROPOSED,
        )

        req_json = json.dumps(req.to_dict(), indent=2, ensure_ascii=False)
        req_file = session.add_item(
            f"requirement---{req.id}",
            req_json,
            suffix=Constant.JSON_FILE_EXT,
        )
        saved.append(req_file)
        log.info(
            "Saved requirement %d to '%s'.",
            item.sentence_id,
            req_file,
        )

    log.info(
        "Converting %d analysis items to requirements OK.",
        len(iso_response.analysis),
    )
    log.info(
        "Staged %d requirement(s) in session '%s'.",
        len(saved),
        session_id,
    )
