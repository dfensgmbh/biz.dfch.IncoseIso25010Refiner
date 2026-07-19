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

"""Shared command lines options."""

from pathlib import Path
from typing import Annotated

import click
import typer

from biz.dfch.i18n import LanguageCode

from ..chat.providers import Providers
from ..iso25010 import Iso25010

ProviderOpt = Annotated[
    Providers,
    typer.Option(
        "--provider",
        "-p",
        envvar="CHAT_PROVIDER",
        help="LLM provider.",
        case_sensitive=False,
    ),
]

ModelOpt = Annotated[
    str,
    typer.Option(
        "--model",
        "-m",
        envvar="CHAT_MODEL",
        help="Specify the model name to use.",
    ),
]

ApiTokenOpt = Annotated[str, typer.Option(envvar="CHAT_API_TOKEN", help="API Token")]

BaseUriOpt = Annotated[
    str,
    typer.Option("--base-url", "-u", "-uri", envvar="CHAT_BASE_URL", help="Base URL"),
]

JiraBaseUriOpt = Annotated[
    str,
    typer.Option("--jira-base-url", envvar="JIRA_BASE_URL", help="Jira Base URL"),
]

JiraProjectKeyOpt = Annotated[
    str,
    typer.Option("--jira-project-key", envvar="JIRA_PROJECT_KEY", help="Jira Project Key"),
]

JiraApiTokenOpt = Annotated[str, typer.Option(envvar="JIRA_API_TOKEN", help="Jira API Token")]

WorkspaceOpt = Annotated[
    Path,
    typer.Option(
        ...,
        "--workspace",
        "-ws",
        exists=True,
        envvar="REQ_WORKSPACE",
        help="The workspace base path. This contains the session folder.",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
]

HfCacheOpt = Annotated[
    Path,
    typer.Option(
        ...,
        "--hf-cache",
        exists=True,
        envvar="HF_CACHE",
        help="The HuggingFace cache path.",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
]

SessionIdOpt = Annotated[
    str,
    typer.Option(
        ...,
        "--session-id",
        "-id",
        envvar="REQ_ID",
        help="A unique session id.",
    ),
]


class CharacteristicsType(click.ParamType):
    """CharacteristicsType"""

    name = " ".join([e.name for e in Iso25010])

    def convert(self, value, param, ctx):
        # Already resolved (for example default value).
        if isinstance(value, Iso25010):
            return value

        # 1) Exact match by name (case-insensitive).
        for member in Iso25010:
            if member.name.lower() == value.lower():
                return member

        # 2) Partial match by name (case-insensitive).
        matches = [member for member in Iso25010 if member.name.lower().startswith(value.lower())]

        if len(matches) == 1:
            return matches[0]

        if len(matches) > 1:
            matched_names = ", ".join(m.name for m in matches)
            self.fail(f"'{value}' is ambiguous. Matches: {matched_names}", param, ctx)

        self.fail(
            f"'{value}' is not a valid choice. Choose from: {', '.join(m.name for m in Iso25010)}",
            param,
            ctx,
        )


CharacteristicsOpt = Annotated[
    list[Iso25010] | None,
    typer.Option(
        "--characteristics",
        "-c",
        click_type=CharacteristicsType(),
        help=(
            "ISO 25010 characteristics. If you do not specify this argument, "
            "we use all characteristics. "
            "You can abbreviate the characteristics. "
            "For example: 'fl', 'FUNC', 'sec'."
        ),
    ),
]

InputOpt = Annotated[
    str,
    typer.Option(
        "--input",
        "-i",
        help="Input text. You can also specify a path to an existing file.",
    ),
]

PromptOpt = Annotated[
    str,
    typer.Option(
        "--prompt",
        "-t",
        help="Prompt text. You can also specify a path to an existing file.",
    ),
]

MaxTokensOpt = Annotated[
    int,
    typer.Option(
        "--max-tokens",
        help="Define the maximum number of tokens for the model.",
    ),
]

TemperateOpt = Annotated[
    int,
    typer.Option(
        "--temperature",
        help="Define the temperature of the model. Valid values are between 0 and 1.",
    ),
]

FileOpt = Annotated[
    Path,
    typer.Option(
        "--file",
        "-i",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Path to an existing file.",
    ),
]

YesOpt = Annotated[
    bool,
    typer.Option(
        "--yes",
        "-y",
        help="Confirm action now and do not ask for extra confirmation.",
    ),
]

QuestionsOpt = Annotated[
    int,
    typer.Option(
        "--questions",
        "-q",
        min=1,
        help="Number of questions to generate per ISO 25010 characteristic.",
    ),
]


class LanguageCodeType(click.ParamType):
    """LanguageCodeType"""

    name = " ".join([e.name for e in LanguageCode])

    def convert(self, value, param, ctx):
        # Already resolved (for example default value).
        if isinstance(value, LanguageCode):
            return value

        # 1) Exact match by name (case-insensitive).
        for member in LanguageCode:
            if member.name.lower() == value.lower():
                return member

        # 2) Partial match by name (case-insensitive).
        matches = [member for member in LanguageCode if member.name.lower().startswith(value.lower())]

        if len(matches) == 1:
            return matches[0]

        if len(matches) > 1:
            matched_names = ", ".join(m.name for m in matches)
            self.fail(f"'{value}' is ambiguous. Matches: {matched_names}", param, ctx)

        self.fail(
            f"'{value}' is not a valid choice. Choose from: {', '.join(m.name for m in LanguageCode)}",
            param,
            ctx,
        )


LanguageOpt = Annotated[
    LanguageCode,
    typer.Option(
        "--language",
        "-l",
        click_type=LanguageCodeType(),
        help="Target language of the operation.",
        case_sensitive=False,
        envvar="REQ_LANGUAGE",
    ),
]
