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

"""Common chat client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .chat_config import ChatConfig


class ChatClientBase(ABC):
    """Common interface for chat clients."""

    _config: ChatConfig

    def __init__(self, config: ChatConfig) -> None:

        super().__init__()

        assert isinstance(config, ChatConfig), type(config)

        self._config = config

    @abstractmethod
    def query(self) -> str:
        """Send a chat query and return the assistant response."""

    @property
    def _encoding(self) -> str:
        """The default encoding for requests and responses."""
        return "utf-8"

    def _build_prompt(self) -> str:
        """
        Build the final prompt from optional template content and user prompt.
        """

        if self._config.template_content is None:
            result = self._config.prompt

            return result

        template = self._config.template_content
        result = template + "<PHRASE>\n" + self._config.prompt + "</PHRASE>\n"

        return result
