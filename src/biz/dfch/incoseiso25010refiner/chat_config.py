# Copyright (C) 2026 Ronald Rink, d-fens GmbH, http://d-fens.ch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
ChatConfig
"""

from __future__ import annotations
import os
from dataclasses import dataclass

import dacite


@dataclass(frozen=True)
class ChatConfig:
    """Chat client configuration."""

    api_token: str
    base_url: str
    model: str
    prompt: str
    temperature: float | None = None
    max_tokens: int | None = None

    @staticmethod
    def from_dict(data: dict) -> ChatConfig:
        """Converts CLI arguments to data structure."""
        return dacite.from_dict(
            data_class=ChatConfig,
            data=data,
            config=dacite.Config(strict=True),
        )

    @staticmethod
    def from_args_and_env(args: dict) -> "ChatConfig":
        """
        Build AppConfig from parsed CLI args dict.
        Falls back to CHAT_API_TOKEN env var if --api-token not provided.
        """
        api_token = args.get("api_token") or os.environ.get("CHAT_API_TOKEN")
        if not api_token:
            raise ValueError(
                "API token must be provided via --api-token or CHAT_API_TOKEN env var."
            )

        data = {
            "api_token": api_token,
            "base_url": args.get("base_url", "https://routellm.abacus.ai/v1"),
            "model": args.get("model", "route-llm"),
            "prompt": args["prompt"],
            "temperature": args.get("temperature", 0.7),
            "max_tokens": args.get("max_tokens"),
        }

        return ChatConfig.from_dict(data)
