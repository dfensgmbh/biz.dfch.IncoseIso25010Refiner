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

from ..chat.providers import Providers
from ..iso25010 import Iso25010

ProviderOpt = Annotated[
    Providers,
    typer.Option(
        "--provider",
        "-p",
        envvar="CHAT_PROVIDER",
        help="LLM provider.",
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

ApiTokenOpt = Annotated[
    str, typer.Option(envvar="CHAT_API_TOKEN", help="API token")
]

BaseUriOpt = Annotated[
    str,
    typer.Option("--base-url", "-uri", envvar="CHAT_BASE_URL", help="Base URL"),
]

WorkspaceOpt = Annotated[
    Path,
    typer.Option(
        ...,
        "--workspace",
        "-ws",
        exists=True,
        envvar="REQ_WORKSPACE",
        help="The workspace base path. " "This contains the session folder.",
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
        # already resolved (e.g. default value)
        if isinstance(value, Iso25010):
            return value

        # 1. exact match by name (case-insensitive).
        for member in Iso25010:
            if member.name.lower() == value.lower():
                return member

        # 2. partial match by name (case-insensitive).
        matches = [
            member
            for member in Iso25010
            if member.name.lower().startswith(value.lower())
        ]

        if len(matches) == 1:
            return matches[0]

        if len(matches) > 1:
            matched_names = ", ".join(m.name for m in matches)
            self.fail(
                f"'{value}' is ambiguous. Matches: {matched_names}", param, ctx
            )

        self.fail(
            f"'{value}' is not a valid choice. Choose from: "
            f"{', '.join(m.name for m in Iso25010)}",
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
        help="Input text. " "You can also specify a path to an existing file.",
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
        help="Define the temperature of the model. "
        "Valid values are between 0 and 1.",
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
        help="Path to an existing input file.",
    ),
]

YesOpt = Annotated[
    bool,
    typer.Option(
        "--yes", "-y", help="Confirm action and do not ask for confirmation."
    ),
]
