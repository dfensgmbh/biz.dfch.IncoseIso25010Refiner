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

"""Constant class."""

from __future__ import annotations
from dataclasses import dataclass

from .text.file_utils import FileUtils


@dataclass
class Constant:
    """System-wide constants."""

    # Note: also change "version" in `pyproject.toml`.
    # Note: also operate `uv lock`.
    _VERSION = "0.1.0"
    PROG_NAME = "IncoseIso25010Refiner"

    SOURCE_DOCUMENT = "source.md"

    PROJECT_ROOT = FileUtils.find_project_root().resolve()
    SRC_DIR = (FileUtils.find_project_root() / "src").resolve()
    PROMPTS_DIR = (FileUtils.find_project_root() / "src" / "prompts").resolve()

    PROMPT_REFINE = "prompt-refine.md"
