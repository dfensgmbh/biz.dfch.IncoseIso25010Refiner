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

"""Legacy refine implementation (Abacus / Ollama providers). To be removed."""

import json
from dataclasses import asdict
from pathlib import Path

from rich.console import Console

from biz.dfch.diagnostics import Stopwatch
from biz.dfch.logging import log
from biz.dfch.i18n import LanguageCode

from ..constant import Constant
from ..chat.chat_client_factory import ChatClientFactory as ChatClientFactoryLegacy
from ..chat.chat_config import ChatConfig as ChatConfigLegacy
from ..chat.instructor_with_lite_llm import InstructorWithLiteLlm as InstructorWithLiteLlmLegacy
from ..parse import parse_iso_response as parse_iso_response_legacy
from ..session import Session
from ..text.text_utils import TextUtils
from ..text.file_utils import FileUtils
from ..console import RichUtils
from ..iso25010 import Iso25010


def refine_legacy(
    api_token: str,
    session_id: str,
    uri: str,
    model: str,
    temperature: int,
    max_tokens: int,
    provider: str,
    workspace: Path,
    characteristics: list[Iso25010],
    language: LanguageCode,
    session: Session,
    console: Console,
) -> None:
    """
    Legacy refine path for Abacus and Ollama providers.

    This function will be removed once the OpenAI provider path is the
    only supported path.
    """

    source_doc = session.source.file
    text = session.source.contents

    # Prepare map for chat configuration.
    data: dict = {
        "provider": provider,
        "base_url": uri,
        "api_token": api_token,
        "model": model,
        "session_id": session_id,
        "output_path": "",
        "prompt": text,
    }
    if -1 != max_tokens:
        data["max_tokens"] = max_tokens
    if -1 != temperature:
        data["temperature"] = temperature

    template_file = Constant.PROMPTS_DIR / Constant.PROMPT_REFINE
    assert template_file.exists(), template_file
    data["template_content"] = template_file.read_text(encoding="utf-8")

    # Prepare client.
    chat_config = ChatConfigLegacy.from_dict(data)
    client = ChatClientFactoryLegacy.create(chat_config)

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
    iso25010_response = parse_iso_response_legacy(text)

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
            translated, _ = InstructorWithLiteLlmLegacy(
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