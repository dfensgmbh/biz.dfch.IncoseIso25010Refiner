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

"""'summary' command."""

from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.markup import escape
import typer

from biz.dfch.diagnostics import Stopwatch
from biz.dfch.logging import log

from ..constant import Constant
from ..chat.chat_client_factory import ChatClientFactory
from ..chat.chat_config import ChatConfig
from ..chat.providers import Providers
from ..info import Info
from ..iso25010 import Iso25010
from ..session import Session
from ..ui.rich_utils import RichUtils

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
def summary(
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
    """
    Make a summary of requirements in the source document.
    """

    assert isinstance(workspace, Path), type(workspace)
    path = Path(workspace / session_id).resolve()
    assert path.exists(), f"Path must exist: '{path}'."

    if characteristics is None:
        characteristics = Iso25010.all()

    if not uri.strip():
        uri = ChatConfig.default_values[provider].base_url

    if not model.strip():
        model = ChatConfig.default_values[provider].model

    log.debug("Get session '%s' ...", session_id)
    session = Session(workspace, session_id)
    log.info("Get session '%s' OK.", session_id)

    text = session.source.contents

    data = {
        "workspace": str(workspace),
        "session_id": session_id,
        "provider": provider,
        "base_url": uri,
        "api_token": 0 < len(api_token),
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "characteristics": characteristics,
    }
    log.debug("Parameters: [escape(str(%s))]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console = Console()
    console.print(table)

    # Prepare map for chat configuration.
    data["api_token"] = api_token
    data["output_path"] = ""
    if -1 == max_tokens:
        del data["max_tokens"]
    if -1 == temperature:
        del data["temperature"]
    template_file = Constant.PROMPTS_DIR / Constant.PROMPT_SUMMARY
    assert template_file.exists(), template_file
    data["template_content"] = template_file.read_text(encoding="utf-8")

    # Prepare client.
    data["prompt"] = text
    chat_config = ChatConfig.from_dict(data)
    client = ChatClientFactory.create(chat_config)

    log.debug("Make summary ...")
    sw = Stopwatch.start_new()
    try:
        response = client.query()
        sw.stop()
    except TimeoutError as ex:
        sw.stop()
        elapsed = sw.elapsed_seconds
        log.error(
            "Make summary FAILED. TotalSeconds: %.3f",
            elapsed,
            exc_info=ex,
        )
        raise

    elapsed = sw.elapsed_seconds
    log.info("Make summary OK. TotalSeconds: %.3f", elapsed)

    summary_doc = session.add_item("summary", response, suffix=".md")

    log.info(
        f"You can find the summary here: '[link=file:///{summary_doc}]"
        f"{summary_doc}[/link]'."
    )
