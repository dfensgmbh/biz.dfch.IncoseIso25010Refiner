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

"""'refine' command."""

import json
from dataclasses import asdict
from pathlib import Path

from rich.console import Console
import typer

from biz.dfch.diagnostics import Clock
from biz.dfch.diagnostics import Stopwatch
from biz.dfch.logging import log

from ..constant import Constant
from ..chat.chat_client_factory import ChatClientFactory
from ..chat.chat_config import ChatConfig
from ..chat.providers import Providers
from ..info import Info
from ..iso25010 import Iso25010
from ..parse import parse_iso_response
from ..text.text_utils import TextUtils
from ..text.file_utils import FileUtils
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

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command()
def refine(
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
    Query the LLM and add questions for refinement.
    """

    assert isinstance(workspace, Path), type(workspace)
    path = workspace / session_id
    assert path.exists(), f"Path does not exist: '{path}'."

    source_doc = path / Constant.SOURCE_DOCUMENT
    assert source_doc.exists(), f"File does not exist: '{source_doc}'."
    assert source_doc.is_file(), f"File is not a file: '{source_doc}'."

    if source_doc.exists() and source_doc.is_file():
        text = source_doc.read_text(encoding="utf-8")
    text = source_doc.read_text(encoding="utf-8")

    if characteristics is None:
        characteristics = list(Iso25010)

    if not uri.strip():
        uri = ChatConfig.default_values[provider].base_url

    if not model.strip():
        model = ChatConfig.default_values[provider].model

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
        "input": text,
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
    data["output_path"] = ""
    if -1 == max_tokens:
        del data["max_tokens"]
    if -1 == temperature:
        del data["temperature"]
    template_file = Constant.PROMPTS_DIR / Constant.PROMPT_REFINE
    assert template_file.exists(), template_file

    data["template_content"] = template_file.read_text(encoding="utf-8")

    # Prepare client.
    chat_config = ChatConfig.from_dict(data)
    client = ChatClientFactory.create(chat_config)

    # Start query.
    start_time = Clock.now_isodate()
    log.debug("Querying LLM ...")
    RichUtils.print(f"{start_time}: Querying LLM ...")
    sw = Stopwatch.start_new()
    try:
        response = client.query()
        sw.stop()
        stop_time = Clock.now_isodate()
    except TimeoutError as ex:
        sw.stop()
        elapsed = sw.elapsed_seconds
        log.error(
            "Querying LLM FAILED. TotalSeconds: %.3f",
            elapsed,
            exc_info=ex,
        )
        RichUtils.error(
            f"{start_time}: Querying LLM FAILED. TotalSeconds: "
            f"{elapsed:.3f}."
        )
        raise

    elapsed = sw.elapsed_seconds
    log.info("Querying LLM OK. TotalSeconds: %.3f", elapsed)
    RichUtils.info(
        f"{stop_time}: Querying LLM OK. TotalSeconds: " f"{elapsed:.3f}."
    )
    timestamp = Clock.now_file()

    # Examine response.
    text = TextUtils.remove_md_json(response)
    text = TextUtils.clean_pseudo_json(text)
    is_json = TextUtils.is_json(text)
    if not is_json:
        text = TextUtils.clean_text(text)
    is_json = TextUtils.is_json(text)

    console = Console()
    # RichUtils.print("Response:")
    # try:
    #     console.print(JSON(text, indent=2))
    # except Exception:  # pylint: disable=W0718  # type:ignore
    #     console.print(Markdown(text))

    # Save response as json or text.
    extension = ".json" if is_json else ".txt"
    response_file = path / f"response---{timestamp}{extension}"
    RichUtils.print(f"Writing response: '{response_file}' ...")
    assert not response_file.exists(), response_file
    response_file.write_text(text, encoding="utf-8")
    RichUtils.info(f"Writing response: '{response_file}' OK.")

    # When we do not have valid JSON, show error message and exit.
    assert is_json, (
        "Response does not contain valid JSON. Try operation one more time.\n"
        f"{TextUtils.get_json_parse_exception(text)}"
    )

    # Parse response.
    iso25010_response = parse_iso_response(text)

    # Display results.
    result = RichUtils.create_analysis_table(iso25010_response.analysis)
    console.print(result)

    # result = RichUtils.create_questions_table(iso25010_response.questions)
    # console.print(result)

    result = RichUtils.create_scores_table(
        iso25010_response.summary.scores, iso25010_response.summary.rationale
    )
    console.print(result)

    result = RichUtils.create_iso25010_chart(iso25010_response.summary.scores)
    console.print(result)

    # Create copy of source document.
    RichUtils.print("Making copy of source document ...")
    source_copy = FileUtils.make_copy(source_doc, f"---{timestamp}")
    assert source_copy.exists(), source_copy
    RichUtils.info(f"Making copy of source document '{source_copy}' OK.")

    # Change source document and add new questions to it.
    updated = FileUtils.update_source_doc(
        source_doc, iso25010_response.questions
    )
    source_doc.write_text(updated, encoding="utf-8")

    # Save summary
    summary_json = json.dumps(asdict(iso25010_response.summary), indent=2)
    summary_doc = path / f"summary---{timestamp}.json"
    summary_doc.write_text(summary_json, encoding="utf-8")

    console.print(
        f"You can now continue your work in: '[link=file:///{source_doc}]"
        f"{source_doc}[/link]'."
    )
