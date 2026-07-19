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

"""'resolve' command."""

from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console

from biz.dfch.diagnostics import Stopwatch
from biz.dfch.logging import log

from ..chat.chat_client_factory import ChatClientFactory
from ..chat.chat_config import ChatConfig
from ..chat.providers import Providers
from ..console import RichUtils
from ..constant import Constant
from ..info import Info
from ..iso25010 import Iso25010
from ..session import Session
from .args import (
    ApiTokenOpt,
    BaseUriOpt,
    CharacteristicsOpt,
    MaxTokensOpt,
    ModelOpt,
    ProviderOpt,
    SessionIdOpt,
    TemperateOpt,
    WorkspaceOpt,
)

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command()
def resolve(
    api_token: ApiTokenOpt,
    session_id: SessionIdOpt,
    uri: BaseUriOpt = "",
    model: ModelOpt = "",
    temperature: TemperateOpt = -1,
    max_tokens: MaxTokensOpt = -1,
    provider: ProviderOpt = Providers.DEFAULT,
    workspace: WorkspaceOpt = Path("."),
    characteristics: CharacteristicsOpt = None,
    keep_questions_without_answer: Annotated[
        bool,
        typer.Option(
            "-k",
            "--keep",
            help="Keep questions without answer in the source document.",
        ),
    ] = False,
):
    """
    Resolve questions in the source document.
    """

    assert isinstance(workspace, Path), type(workspace)
    path = Path(workspace / session_id).resolve()
    assert path.exists(), f"Path must exist: '{path}'."

    assert isinstance(keep_questions_without_answer, bool), type(
        keep_questions_without_answer
    )

    if characteristics is None:
        characteristics = Iso25010.all()

    if not uri.strip():
        uri = ChatConfig.default_values[provider].base_url

    if not model.strip():
        model = ChatConfig.default_values[provider].model

    log.debug("Get session '%s' ...", session_id)
    session = Session(workspace, session_id)
    log.info("Get session '%s' OK.", session_id)

    lines = session.source.lines
    questions = session.source.get_questions()
    questions_with_answer = [q for q in questions if q.has_answer()]

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
        "keep": keep_questions_without_answer,
        "questions": "\n".join(
            [f"[{q.idx + 1}] {q.question}" for q in questions_with_answer]
        ),
    }
    log.debug("Parameters: [%s]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console = Console()
    console.print(table)

    if 0 == len(questions_with_answer):
        log.info("No questions with answers to resolve.")
        return

    # Prepare map for chat configuration.
    del data["questions"]
    data["api_token"] = api_token
    data["output_path"] = ""
    if -1 == max_tokens:
        del data["max_tokens"]
    if -1 == temperature:
        del data["temperature"]
    template_file = Constant.PROMPTS_DIR / Constant.PROMPT_RESOLVE
    assert template_file.exists(), template_file
    data["template_content"] = template_file.read_text(encoding="utf-8")

    requirements: dict[int, str] = {}
    for q in questions:
        if not q.has_answer():
            continue

        line_number = q.idx + 1

        # Start query.
        log.debug("Resolve question [%s] ...", line_number)

        # Prepare client.
        data["prompt"] = f"{q.question}\n{'\n'.join(q.answer)}"
        chat_config = ChatConfig.from_dict(data)
        client = ChatClientFactory.create(chat_config)

        log.debug(data["prompt"])
        sw = Stopwatch.start_new()
        try:
            requirement = client.query()
            sw.stop()
            log.info(requirement)
            requirements[q.idx] = requirement
        except TimeoutError as ex:
            sw.stop()
            elapsed = sw.elapsed_seconds
            log.error(
                "Resolve question [%s] FAILED. TotalSeconds: %.3f",
                line_number,
                elapsed,
                exc_info=ex,
            )

        elapsed = sw.elapsed_seconds
        log.info(
            "Resolve question [%s] OK. TotalSeconds: %.3f", line_number, elapsed
        )

    # Now replace the original question and answers with the merged responses.
    first = -1
    last = len(lines) - 1
    decrement = -1
    for i in range(last, first, decrement):
        if not keep_questions_without_answer:
            qr = next(
                (q for q in questions if q.idx == i and not q.has_answer()),
                None,
            )
            if qr is not None:
                log.debug("[%s] Remove question without answer.", i)
                lines[i] = ""
                continue

        if i not in requirements:
            continue

        question = next((q for q in questions if q.idx == i), None)
        assert question is not None, (
            f"Logic error. Question index not valid: {i}."
        )

        log.debug(
            "Merge question and answer [%s] ...",
            question.idx + 1,
        )
        for j in range(question.end, question.idx, -1):
            log.debug("[%s] Remove answer: '%s'.", j, lines[j])
            del lines[j]

        requirement = requirements[i]
        log.debug("[%s] Remove question: '%s'.", i, lines[i])
        del lines[i]
        log.debug("[%s] Add requirement: '%s'.", i, requirement)
        lines.insert(i, requirement)

        log.info(
            "Merge question and answer [%s] OK.",
            question.idx + 1,
        )

        # Examine if the previous line is another question.
        # Then, insert two empty lines.
        if i > 0 and lines[i - 1].startswith(">"):
            lines.insert(i, "")
            lines.insert(i, "")
            log.debug("[%s] Insert double line padding.", i)
            continue

        # Examine if there is a question within the two consecutive previous
        # lines.
        # Then, insert one empty line.
        if (
            i > 1
            and lines[i - 1].strip() == ""
            and lines[i - 2].startswith(">")
        ):
            lines.insert(i, "")
            log.debug("[%s] Insert single line padding.", i)
            continue

    contents = "\n".join(lines)
    session.source.update(contents, do_add_version=True)

    log.info(
        "You can now continue your work in: "
        f"'{RichUtils.make_link(session.source.file)}'"
    )
