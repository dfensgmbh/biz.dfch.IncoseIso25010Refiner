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

"""'translate' command."""

from pathlib import Path

import instructor
from pydantic import BaseModel, Field
from rich.console import Console
import typer
from dotenv import load_dotenv

from biz.dfch.diagnostics import Stopwatch
from biz.dfch.i18n import LanguageCode
from biz.dfch.logging import log

from ..chat.ai_token_usage import AiTokenUsage
from ..chat.providers import Providers
from ..chat.zero_cost_map import ZeroCostMap
from ..chat.chat_config import ChatConfig
from ..info import Info
from ..session import Session
from ..ui.rich_utils import RichUtils

from .args import ApiTokenOpt
from .args import BaseUriOpt
from .args import InputOpt
from .args import CharacteristicsOpt
from .args import MaxTokensOpt
from .args import ModelOpt
from .args import ProviderOpt
from .args import SessionIdOpt
from .args import TemperateOpt
from .args import WorkspaceOpt
from .args import LanguageOpt


class TranslationResponse(BaseModel):
    """Schema for translation response."""

    original_text: str = Field(description="The original text provided")
    translated_text: str = Field(description="The translated text")
    detected_language: str = Field(
        description="ISO 639-1 language code of original text"
    )


load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


def translate(
    api_token: ApiTokenOpt,
    session_id: SessionIdOpt,
    text: InputOpt,
    uri: BaseUriOpt = "",
    model: ModelOpt = "",
    temperature: TemperateOpt = -1,
    max_tokens: MaxTokensOpt = -1,
    provider: ProviderOpt = Providers.DEFAULT,
    workspace: WorkspaceOpt = Path("."),
    characteristics: CharacteristicsOpt = None,
    language: LanguageOpt = LanguageCode.EN,
):
    """
    Translate text using litellm and instructor (Structured Outputs).
    """

    assert "/" not in model, model

    log.debug("Get session '%s' ...", session_id)
    session = Session(workspace, session_id)
    log.info("Get session '%s' OK.", session_id)

    assert text.strip()
    input_file = Path(session.path / text).resolve()
    if input_file.exists() and input_file.is_file():
        text = input_file.read_text(encoding="utf-8")

    from litellm import completion, litellm  # pylint: disable=C0415

    litellm.model_cost = ZeroCostMap(litellm.model_cost)

    model = f"openai/{model}"

    if not uri.strip():
        uri = ChatConfig.default_values[provider].base_url
    if not uri.endswith("/v1"):
        uri = f"{uri}/v1"
    if not model.strip():
        model = f"openai/{ChatConfig.default_values[provider].model}"

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
        "input": text,
    }

    log.debug("Parameters: [%s]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console = Console()
    console.print(table)

    log.debug("Translate text to '%s' ...", language.value)

    # Initialize instructor with litellm
    client = instructor.from_litellm(
        completion,
        mode=instructor.Mode.MD_JSON,
    )

    sw = Stopwatch.start_new()
    try:
        # response = client.chat.completions.create(
        response, raw = client.create_with_completion(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a requirements engineer and "
                        "professional translator. "
                        f"Translate the input to {language.value}."
                    ),
                },
                {"role": "user", "content": text},
            ],
            response_model=TranslationResponse,
            api_key=api_token,
            base_url=uri,
        )
        sw.stop()

        data = AiTokenUsage.from_response(raw)
        log.debug("Parameters: [%s]", data)
        table = RichUtils.make_table(
            data,
            title="Parameters",
        )

        console = Console()
        console.print(table)

        elapsed = sw.elapsed_seconds
        log.info(
            "Translate text to '%s' OK. TotalSeconds: %.3f",
            language.value,
            elapsed,
        )

        file = session.add_item(
            f"summary-{language.name}", response.translated_text, ".md"
        )

        log.info(
            "You can now continue your work in: "
            f"'{RichUtils.make_link(file)}'"
        )

    except TimeoutError as ex:
        sw.stop()
        elapsed = sw.elapsed_seconds
        log.error(
            "Query LLM FAILED. TotalSeconds: %.3f",
            elapsed,
            exc_info=ex,
        )
        raise
    except Exception as ex:
        sw.stop()
        elapsed = sw.elapsed_seconds
        log.error(
            "Translate text to '%s' FAILED. TotalSeconds: %.3f",
            elapsed,
            language.value,
            exc_info=ex,
        )
        raise typer.Exit(code=1)
