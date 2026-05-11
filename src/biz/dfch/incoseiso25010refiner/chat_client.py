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
ChatClient module for querying the Abacus ChatLLM API.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .chat_config import ChatConfig


class ChatClient:
    """Sends prompts to the Abacus ChatLLM API and returns the response."""

    _cfg: ChatConfig

    def __init__(self, cfg: ChatConfig) -> None:
        assert isinstance(cfg, ChatConfig), type(cfg)

        self._cfg = cfg

    def query(self) -> str:
        """Send the prompt to the API and return the assistant response text."""
        url = f"{self._cfg.base_url}/chat/completions"

        if self._cfg.template_content is None:
            template = ""
        else:
            template = self._cfg.template_content
        content = (
            template + "<PHRASE>\n" + self._cfg.prompt + "</PHRASE>\n"
        )
        payload: dict = {
            "model": self._cfg.model,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
        }

        if self._cfg.temperature is not None:
            payload["temperature"] = self._cfg.temperature

        if self._cfg.max_tokens is not None:
            payload["max_tokens"] = self._cfg.max_tokens

        request = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._cfg.api_token}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (compatible; IncoseIso25010Refiner/1.0)",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"API request failed: HTTP {e.code} {e.reason} — {body}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"API request failed: {e.reason}") from e

        return data["choices"][0]["message"]["content"]
