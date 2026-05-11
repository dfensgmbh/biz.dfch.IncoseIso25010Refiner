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
Abacus chatConfig
"""

from __future__ import annotations

from dataclasses import dataclass

from .default_chat_config import DefaultChatConfig


@dataclass(frozen=True)
class AbacusChatConfig(DefaultChatConfig):
    """Ollama chat client configuration."""

    base_url: str = "https://routellm.abacus.ai/v1"
    model: str = "route-llm"
