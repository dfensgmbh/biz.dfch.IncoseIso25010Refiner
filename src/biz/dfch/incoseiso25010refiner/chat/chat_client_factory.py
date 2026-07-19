# Copyright (c) 2026 Ronald Rink, http://d-fens.ch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Chat client factory module."""

from __future__ import annotations

from .abacus_chat_client import AbacusChatClient
from .chat_client_base import ChatClientBase
from .chat_config import ChatConfig, Providers
from .ollama_chat_client import OllamaChatClient


class ChatClientFactory:
    """Creates chat client instances."""

    @staticmethod
    def create(config: ChatConfig) -> ChatClientBase:
        """Create a chat client for the selected provider."""

        assert isinstance(config, ChatConfig), type(config)
        assert config.provider in Providers, config.provider

        if config.provider == Providers.ABACUS:
            return AbacusChatClient(config)

        if config.provider == Providers.OLLAMA:
            return OllamaChatClient(config)

        raise ValueError(f"Incorrect chat provider: '{config.provider}'.")
