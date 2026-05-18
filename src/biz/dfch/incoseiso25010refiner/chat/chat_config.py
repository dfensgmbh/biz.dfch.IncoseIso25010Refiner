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

"""
ChatConfig
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
from typing import ClassVar

import dacite

from .abacus_chat_config import AbacusChatConfig
from .default_chat_config import DefaultChatConfig
from .ollama_chat_config import OllamaChatConfig
from .providers import Providers


@dataclass(frozen=True)
class ChatConfig:
    """Chat client configuration."""

    default_values: ClassVar[dict[Providers, DefaultChatConfig]] = {
        Providers.ABACUS: AbacusChatConfig(),
        Providers.OLLAMA: OllamaChatConfig(),
    }
    provider: Providers
    api_token: str
    base_url: str
    model: str
    prompt: str
    session_id: str
    output_path: str
    temperature: float | None = None
    max_tokens: int | None = None
    template: str | None = None
    template_content: str = ""

    @staticmethod
    def from_dict(data: dict) -> "ChatConfig":
        """Converts CLI arguments to data structure."""
        return dacite.from_dict(
            data_class=ChatConfig,
            data=data,
            config=dacite.Config(
                strict=False,
                cast=[Providers],
            ),
        )

    @staticmethod
    def from_args_and_env(args: argparse.Namespace) -> ChatConfig:
        """
        Build ChatConfig from parsed CLI args.

        Falls back to CHAT_API_TOKEN env var if --api-token not provided.
        """

        provider = getattr(args, "provider", Providers.DEFAULT)
        if provider not in Providers:
            raise ValueError(f"Incorrect chat provider: '{provider}'.")

        api_token = getattr(args, "api_token", "") or os.environ.get(
            "CHAT_API_TOKEN"
        )
        if not api_token and Providers.OLLAMA == provider:
            raise ValueError(
                "API token must be provided via --api-token or "
                "CHAT_API_TOKEN environment variable."
            )

        template = getattr(args, "template", None)
        template_text = ""

        if template:
            template_file = Path(template)
            assert template_file.is_file(), template_file

            template_text = Path(template_file).read_text(encoding="utf-8")

        base_url = getattr(
            args, "base_url", ChatConfig.default_values[provider].base_url
        )
        if not base_url.strip():
            base_url = ChatConfig.default_values[provider].base_url

        model = getattr(
            args, "model", ChatConfig.default_values[provider].model
        )
        if not model.strip():
            model = ChatConfig.default_values[provider].model

        data = {
            "provider": provider,
            "api_token": api_token,
            "base_url": base_url,
            "model": model,
            "prompt": args.prompt,
            "session_id": args.session,
            "output_path": args.output,
            "temperature": getattr(args, "temperature", None),
            "max_tokens": getattr(args, "max_tokens", None),
            "template": template,
            "template_content": template_text,
        }

        return ChatConfig.from_dict(data)
