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

"""TextUtils class."""

import json
import re
import unicodedata


class TextUtils:
    """TextUtils"""

    @staticmethod
    def remove_md_json(response: str) -> str:
        """Removes markdown JSON formatting from specified text."""

        # Use regex to find content between ```json and ``` or just ``` and ```
        # The [^`]*? is a non-greedy match for everything that isn't a backtick
        pattern = r"```(?:json)?\s*(.*?)\s*```"
        match = re.search(pattern, response, re.DOTALL)

        if match:
            result = match.group(1).strip()
        else:
            # Fallback: model might have returned naked JSON or failed the block
            result = response.strip()

        return result

    @staticmethod
    def clean_text(s: str) -> str:
        """Cleans special characters from specified text."""

        _invisible_chars = re.compile(r"[\u200B-\u200D\u2060\uFEFF]")

        s = unicodedata.normalize("NFC", s)
        s = _invisible_chars.sub("", s)
        s = "".join(ch for ch in s if ch in "\t\n\r" or ord(ch) >= 0x20)

        return s.strip()

    @staticmethod
    def is_json(text: str) -> bool:
        """Examine if the given text is valid JSON."""
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
            return False

    @staticmethod
    def get_json_parse_exception(text: str) -> str:
        """get_json_parse_exception"""
        try:
            json.loads(text)
            return ""
        except Exception as ex:  # pylint: disable=W0718
            return str(ex)

    @staticmethod
    def clean_pseudo_json(text: str) -> str:
        """clean_pseudo_json"""

        assert isinstance(text, str), type(str)

        # Allowed starting characters/sequences for valid JSON lines
        # (after stripping whitespace).
        allowed_pattern = re.compile(r'^[0-9\-\{\}\[\]\,"tf n]')

        cleaned_lines = []

        for line in text.splitlines():
            stripped_line = line.strip()

            if not stripped_line:
                continue

            # Check if the line starts with an allowed JSON character
            if allowed_pattern.match(stripped_line):
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)
