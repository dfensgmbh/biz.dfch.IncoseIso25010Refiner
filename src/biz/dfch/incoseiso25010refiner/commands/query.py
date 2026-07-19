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

"""'query' command."""

import uuid
from pathlib import Path

import typer
from rich.console import Console
from rich.json import JSON
from rich.markdown import Markdown

from biz.dfch.diagnostics import Stopwatch
from biz.dfch.logging import log

from ..chat.chat_client_factory import ChatClientFactory
from ..chat.chat_config import ChatConfig
from ..chat.providers import Providers
from ..console import RichUtils
from ..info import Info
from ..text.text_utils import TextUtils
from .args import (
    ApiTokenOpt,
    BaseUriOpt,
    InputOpt,
    MaxTokensOpt,
    ModelOpt,
    PromptOpt,
    ProviderOpt,
    TemperateOpt,
)

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command()
def query(  # noqa: PLR0913, PLR0915
    api_token: ApiTokenOpt,
    text: InputOpt,
    template: PromptOpt = "",
    uri: BaseUriOpt = "",
    model: ModelOpt = "",
    temperature: TemperateOpt = -1,
    max_tokens: MaxTokensOpt = -1,
    provider: ProviderOpt = Providers.DEFAULT,
):
    """
    Query the LLM and show response.
    """

    assert text.strip()

    input_file = Path(text)
    if input_file.exists() and input_file.is_file():
        text = input_file.read_text(encoding="utf-8")

    template_file = Path(template)
    if template_file.exists() and template_file.is_file():
        template = template_file.read_text(encoding="utf-8")

    if not uri.strip():
        uri = ChatConfig.default_values[provider].base_url

    if not model.strip():
        model = ChatConfig.default_values[provider].model

    data = {
        "provider": provider,
        "base_url": uri,
        "api_token": 0 < len(api_token),
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "input": text,
        "template": str(template_file),
    }
    log.debug("Parameters: [%s]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console = Console()
    console.print(table)

    # Prepare map for chat configuration.
    del data["input"]
    data["prompt"] = text
    data["api_token"] = api_token
    if -1 == max_tokens:
        del data["max_tokens"]
    if -1 == temperature:
        del data["temperature"]

    data["template_content"] = template
    data["session_id"] = str(uuid.uuid4())
    data["output_path"] = str(Path("."))

    # Prepare client.
    chat_config = ChatConfig.from_dict(data)
    client = ChatClientFactory.create(chat_config)

    # Start query.
    log.debug("Query LLM ...")
    sw = Stopwatch.start_new()
    try:
        response = client.query()
        sw.stop()
    except TimeoutError as ex:
        sw.stop()
        elapsed = sw.elapsed_seconds
        log.error(
            "Query LLM FAILED. TotalSeconds: %.3f",
            elapsed,
            exc_info=ex,
        )
        raise

    elapsed = sw.elapsed_seconds
    log.info("Query LLM OK. TotalSeconds: %.3f.", elapsed)

    # Examine response.
    text = TextUtils.remove_md_json(response)
    text = TextUtils.clean_pseudo_json(text)
    is_json = TextUtils.is_json(text)
    if not is_json:
        text = TextUtils.clean_text(text)
    is_json = TextUtils.is_json(text)

    log.info("Response:")
    try:
        console.print(JSON(text, indent=2))
    except Exception:  # pylint: disable=W0718  # type:ignore
        console.print(Markdown(text))
