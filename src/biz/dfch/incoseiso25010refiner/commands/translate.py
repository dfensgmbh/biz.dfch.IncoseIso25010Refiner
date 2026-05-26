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

from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Annotated

import instructor
from pydantic import BaseModel, Field
from rich.console import Console
import typer
from dotenv import load_dotenv

from biz.dfch.diagnostics import Stopwatch
from biz.dfch.logging import log

from ..chat.providers import Providers
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


class AiTokenUsage:
    """
    Extracts and normalizes AI token usage from a LiteLLM / Instructor
    raw response.
    """

    @staticmethod
    def _read(obj, key, default=None):
        if obj is None:
            return default
        if isinstance(obj, Mapping):
            return obj.get(key, default)
        return getattr(obj, key, default)

    @staticmethod
    def _q(value):
        return "?" if value is None else value

    @staticmethod
    def from_response(raw_response) -> dict[str, object]:
        """
        Extract token usage from a LiteLLM / Instructor raw response
        into a flat dict.
        Missing or null values are replaced with '?'.

        Usage:
            tokens = AiTokenUsage.from_response(raw_response)
        """
        r = AiTokenUsage._read
        q = AiTokenUsage._q

        usage = r(raw_response, "usage", {})
        ctd = r(usage, "completion_tokens_details", {})
        ptd = r(usage, "prompt_tokens_details", {})

        return {
            "prompt_tokens": q(r(usage, "prompt_tokens")),
            "completion_tokens": q(r(usage, "completion_tokens")),
            "total_tokens": q(r(usage, "total_tokens")),
            "input_tokens": q(r(usage, "input_tokens")),
            "output_tokens": q(r(usage, "output_tokens")),
            "raw_input_tokens": q(r(usage, "raw_input_tokens")),
            "accepted_prediction_tokens": q(
                r(ctd, "accepted_prediction_tokens")
            ),
            "completion_audio_tokens": q(r(ctd, "audio_tokens")),
            "reasoning_tokens": q(r(ctd, "reasoning_tokens")),
            "rejected_prediction_tokens": q(
                r(ctd, "rejected_prediction_tokens")
            ),
            "prompt_audio_tokens": q(r(ptd, "audio_tokens")),
            "cached_tokens": q(r(ptd, "cached_tokens")),
        }


class Language(str, Enum):
    """Language codes for translation."""

    EN = "EN"
    DE = "DE"
    FR = "FR"


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


class ZeroCostMap(dict):
    """A dictionary that returns a default cost for any missing model."""

    DEFAULT_COST = {
        "max_tokens": 128000,
        "input_cost_per_token": 0.0,
        "output_cost_per_token": 0.0,
        "litellm_provider": "openai",
        "mode": "chat",
    }

    def __getitem__(self, key):
        return super().get(key, self.DEFAULT_COST)

    def get(self, key, default=None):
        return super().get(key, self.DEFAULT_COST)

    def __contains__(self, key):
        # This is the 'Wildcard' trick: tell LiteLLM we HAVE every model
        return True


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
    language: Annotated[
        Language, typer.Option("--target", "-l", help="Target language")
    ] = Language.EN,
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
                    "content": f"You are a requirements engineer and professional translator. Translate the input to {language.value}.",
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
            f"summary-{language}", response.translated_text, ".md"
        )

        log.info(
            f"You can now continue your work in: '[link=file:///{file}]"
            f"{file}[/link]'."
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
