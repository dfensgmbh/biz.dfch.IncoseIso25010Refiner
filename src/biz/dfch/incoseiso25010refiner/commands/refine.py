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

from dotenv import load_dotenv
from rich.console import Console
import typer

from biz.dfch.diagnostics import Stopwatch
from biz.dfch.logging import log

from ..constant import Constant
from ..chat.chat_client_factory import ChatClientFactory
from ..chat.chat_config import ChatConfig
from ..chat.instructor_with_lite_llm import InstructorWithLiteLlm
from ..chat.providers import Providers
from ..info import Info
from ..iso25010 import Iso25010
from ..parse import parse_iso_response
from ..session import Session
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
from .args import LanguageCode
from .args import LanguageOpt

load_dotenv()

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
    language: LanguageOpt = LanguageCode.DE,
):
    """
    Query the LLM and add questions for refinement.
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

    source_doc = session.source.file
    text = session.source.contents

    data = {
        "workspace": RichUtils.make_link(workspace),
        "session_id": RichUtils.make_link(session.path, session_id),
        "provider": provider,
        "base_url": uri,
        "api_token": 0 < len(api_token),
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "characteristics": characteristics,
        "language": language,
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
    del data["language"]
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
    log.info("Query LLM OK. TotalSeconds: %.3f", elapsed)

    # Examine response.
    text = TextUtils.remove_md_json(response)
    text = TextUtils.clean_pseudo_json(text)
    is_json = TextUtils.is_json(text)
    if not is_json:
        text = TextUtils.clean_text(text)
    is_json = TextUtils.is_json(text)

    session.add_response(text)

    # When we do not have valid JSON, show error message and exit.
    assert is_json, (
        "Response does not contain valid JSON. Try operation one more time.\n"
        f"{TextUtils.get_json_parse_exception(text)}"
    )

    # Parse response.
    iso25010_response = parse_iso_response(text)

    if LanguageCode.EN != language:
        count = len(iso25010_response.questions)
        for i, q in enumerate(iso25010_response.questions):
            log.debug(
                "[%s/%s] Translate to '%s': '%s' ...",
                i,
                count,
                language.name,
                q.question,
            )
            translated, _ = InstructorWithLiteLlm(
                response_model=str,
                api_key=api_token,
                base_url=uri,
                model=model,
                system_prompt=(
                    "You are a requirements engineer and "
                    "professional translator. "
                    f"Translate the input to {language.value}. "
                    "Return only the translated text, nothing else."
                ),
                user_prompt=q.question,
            ).complete()
            log.info(
                "[%s/%s] Translate to '%s': '%s' OK.",
                i,
                count,
                language.name,
                q.question,
            )
            q.question = translated

    # Display results.
    result = RichUtils.create_analysis_table(iso25010_response.analysis)
    console.print(result)

    result = RichUtils.create_scores_table(
        iso25010_response.summary.scores, iso25010_response.summary.rationale
    )
    console.print(result)

    result = RichUtils.create_iso25010_chart(iso25010_response.summary.scores)
    console.print(result)

    # Create copy of source document,
    # then change source document and add new questions to it.
    updated = FileUtils.update_source_doc(
        source_doc, iso25010_response.questions
    )
    session.source.update(updated, do_add_version=True)

    # Save summary.
    summary_json = json.dumps(asdict(iso25010_response.summary), indent=2)
    session.add_item("refine-summary", summary_json, Constant.JSON_FILE_EXT)

    log.info(
        "You can now continue your work in: "
        f"'{RichUtils.make_link(session.source.file)}'"
    )
