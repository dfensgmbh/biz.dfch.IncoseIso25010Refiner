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

from pathlib import Path

import typer
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich.console import Console

from biz.dfch.diagnostics import Stopwatch
from biz.dfch.logging import log

from ..chat.chat_config import ChatConfig
from ..chat.providers import Providers
from ..console import RichUtils
from ..constant import Constant
from ..info import Info
from ..iso25010 import Iso25010
from ..models import IsoResponse
from ..prompt_builder import get_prompt
from ..session import Session
from ..text.file_utils import FileUtils
from .args import (
    ApiTokenOpt,
    BaseUriOpt,
    CharacteristicsOpt,
    LanguageCode,
    LanguageOpt,
    MaxTokensOpt,
    ModelOpt,
    ProviderOpt,
    QuestionsOpt,
    SessionIdOpt,
    TemperateOpt,
    WorkspaceOpt,
)
from .refine_legacy import refine_legacy

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command()
def refine(  # noqa: PLR0913
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
    questions: QuestionsOpt = 5,
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
        "input": session.source.contents,
    }
    log.debug("Parameters: [%s]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console = Console()
    console.print(table)

    if provider != Providers.OPENAI:
        refine_legacy(
            api_token=api_token,
            session_id=session_id,
            uri=uri,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=provider,
            workspace=workspace,
            characteristics=characteristics,
            language=language,
            session=session,
            console=console,
        )
        return

    # NOTE: This is the new "openai" provider implementation.
    text = session.source.contents
    source_doc = session.source.file

    template_content = get_prompt(
        template=Constant.PROMPT_REFINE,
        characteristics=characteristics,
        language=language,
        questions=questions,
    )

    # Build and run the agent.
    pydantic_ai_model = OpenAIChatModel(
        model,
        provider=OpenAIProvider(
            base_url=uri,
            api_key=api_token,
        ),
    )
    agent = Agent(
        pydantic_ai_model,
        system_prompt=template_content,
        retries=3,
    )

    log.debug("Query LLM ...")
    sw = Stopwatch.start_new()
    try:
        result = agent.run_sync(text, output_type=IsoResponse)
        sw.stop()
    except Exception as ex:
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

    iso25010_response: IsoResponse = result.output
    assert isinstance(iso25010_response, IsoResponse), type(iso25010_response)

    # Persist the response as JSON.
    session.add_response(iso25010_response.model_dump_json(indent=2))

    # Display results.
    result_table = RichUtils.create_analysis_table(iso25010_response.analysis)
    console.print(result_table)

    result_table = RichUtils.create_scores_table(
        iso25010_response.summary.scores,
        iso25010_response.summary.rationale,
    )
    console.print(result_table)

    result_table = RichUtils.create_iso25010_chart(
        iso25010_response.summary.scores
    )
    console.print(result_table)

    # Create copy of source document,
    # then change source document and add new questions to it.
    updated = FileUtils.update_source_doc(
        source_doc, iso25010_response.questions
    )
    session.source.update(updated, do_add_version=True)

    # Save summary.
    session.add_item(
        "refine-summary",
        iso25010_response.summary.model_dump_json(indent=2),
        Constant.JSON_FILE_EXT,
    )

    log.info(
        "You can now continue your work in: "
        f"'{RichUtils.make_link(session.source.file)}'"
    )
