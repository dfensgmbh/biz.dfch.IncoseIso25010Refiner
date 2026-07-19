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
AiTokenUsage: extracts and normalizes AI token usage from a
LiteLLM / Instructor raw response.
"""

from collections.abc import Mapping


class AiTokenUsage:
    """
    Extracts and normalizes AI token usage from a LiteLLM / Instructor
    raw response.
    """

    @staticmethod
    def _read(obj, key, default=None):
        if obj is None:
            return default
        if isinstance(obj, Mapping):
            return obj.get(key, default)
        return getattr(obj, key, default)

    @staticmethod
    def _q(value):
        return "?" if value is None else value

    @staticmethod
    def from_response(raw_response) -> dict[str, object]:
        """
        Extract token usage from a LiteLLM / Instructor raw response
        into a flat dict.
        Missing or null values are replaced with '?'.

        Usage:
            tokens = AiTokenUsage.from_response(raw_response)
        """
        r = AiTokenUsage._read
        q = AiTokenUsage._q

        usage = r(raw_response, "usage", {})
        ctd = r(usage, "completion_tokens_details", {})
        ptd = r(usage, "prompt_tokens_details", {})

        return {
            "prompt_tokens": q(r(usage, "prompt_tokens")),
            "completion_tokens": q(r(usage, "completion_tokens")),
            "total_tokens": q(r(usage, "total_tokens")),
            "input_tokens": q(r(usage, "input_tokens")),
            "output_tokens": q(r(usage, "output_tokens")),
            "raw_input_tokens": q(r(usage, "raw_input_tokens")),
            "accepted_prediction_tokens": q(r(ctd, "accepted_prediction_tokens")),
            "completion_audio_tokens": q(r(ctd, "audio_tokens")),
            "reasoning_tokens": q(r(ctd, "reasoning_tokens")),
            "rejected_prediction_tokens": q(r(ctd, "rejected_prediction_tokens")),
            "prompt_audio_tokens": q(r(ptd, "audio_tokens")),
            "cached_tokens": q(r(ptd, "cached_tokens")),
        }
