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

"""prompt package."""

import os
from functools import cache
from pathlib import Path

import yaml

from .constant import Constant


class Prompt:
    """Loads and renders prompt templates from the filesystem."""

    ROOT_PATH_VAR = Constant.SRC_DIR

    def __init__(self, config_path: str | Path):
        self._config_path = Path(config_path)
        with open(self._config_path, encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def _resolve_path(self, rel_or_abs: str) -> Path:
        path = Path(rel_or_abs)
        if path.is_absolute():
            return path
        root = os.environ.get(self.ROOT_PATH_VAR)
        if not root:
            raise OSError(f"Prompt path '{rel_or_abs}' is relative but env var '{self.ROOT_PATH_VAR}' is not set.")
        return Path(root) / path

    @cache  # pylint: disable=W1518
    def _load_template(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def render(self, name: str, **kwargs) -> str:
        """
        Load and render a named prompt template.

        Usage:
            prompt.render("translate", param1="text1", arg2="text2")
        """
        raw_path = self._config["prompts"][name]
        resolved = self._resolve_path(raw_path)
        template = self._load_template(str(resolved))
        return template.format(**kwargs)

    def __call__(self, name: str, **kwargs) -> str:
        """Shorthand for render()."""
        return self.render(name, **kwargs)
