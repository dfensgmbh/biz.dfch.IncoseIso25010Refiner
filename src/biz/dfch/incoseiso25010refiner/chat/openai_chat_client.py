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

"""
OpenAI ChatLLM client.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .chat_client_base import ChatClientBase


class OpenAiChatClient(ChatClientBase):
    """Sends prompts to the OpenAI ChatLLM API and returns the response."""

    def query(self) -> str:
        """
        Send the prompt to the OpenAI API and return the assistant response
        text.
        """

        url = f"{self._config.base_url.rstrip('/')}/chat/completions"

        payload: dict = {
            "model": self._config.model,
            "messages": [
                {
                    "role": "user",
                    "content": self._build_prompt(),
                }
            ],
        }

        if self._config.temperature is not None:
            payload["temperature"] = self._config.temperature

        if self._config.max_tokens is not None:
            payload["max_tokens"] = self._config.max_tokens

        request = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode(self._encoding),
            headers={
                "Authorization": f"Bearer {self._config.api_token}",
                "Content-Type": "application/json",
                "User-Agent": (
                    "Mozilla/5.0 (compatible; IncoseIso25010Refiner/1.0)"
                ),
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode(self._encoding))
        except urllib.error.HTTPError as e:
            body = e.read().decode(self._encoding, errors="replace")
            raise RuntimeError(
                f"OpenAI API request failed: HTTP {e.code} {e.reason} — {body}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"OpenAI API request failed: {e.reason}") from e

        return data["choices"][0]["message"]["content"]
