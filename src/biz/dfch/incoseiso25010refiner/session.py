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

"""Session class."""

from __future__ import annotations
from pathlib import Path
import shutil

from biz.dfch.logging import log

from .constant import Constant
from .iso25010 import Iso25010


class Session:
    """
    The session when you work with a requirement set.
    """

    _workspace: Path
    _name: str
    _path: Path
    _source: Path

    def __init__(self, workspace: Path, name: str) -> None:
        """Create an existing session with specified workspace and name."""

        assert isinstance(workspace, Path), type(workspace)
        assert workspace.exists(), f"Workspace must exist: '{workspace}'."
        assert workspace.is_dir(), f"Workspace must be a path: '{workspace}'."

        assert isinstance(name, str), type(name)
        assert name.strip()

        path = Path((workspace) / name).resolve()
        assert path.exists(), f"Path must exist: '{path}'."
        assert path.is_dir(), f"Path must be a path: '{path}'."

        source_doc = Path(Path(path) / Constant.SOURCE_DOCUMENT).resolve()
        assert (
            source_doc.exists()
        ), f"Source document must exist: '{source_doc}'."
        assert source_doc.is_file(), f"Source must be a file: '{source_doc}'."

        self._workspace = workspace.resolve()
        self._name = name
        self._path = path
        self._source = source_doc

    @property
    def source(self) -> Path:
        """Return the source document path of this session."""

        return self._source

    @staticmethod
    def is_valid(workspace: Path, name: str) -> bool:
        """Show if the specified session in workspace is valid."""

        assert isinstance(workspace, Path), type(workspace)
        assert workspace.exists(), f"Workspace must exist: '{workspace}'."
        assert workspace.is_dir(), f"Workspace must be a path: '{workspace}'."

        assert isinstance(name, str), type(name)
        assert name.strip()

        path = Path((workspace) / name).resolve()
        assert path.exists(), f"Path must exist: '{path}'."
        assert path.is_dir(), f"Path must be a path: '{path}'."

        source = Path(Path(path) / Constant.SOURCE_DOCUMENT).resolve()

        result = source.exists() and source.is_file()

        return result

    @staticmethod
    def all(workspace: Path) -> list[Path]:
        """Return a list of session paths in the specified workspace."""

        assert isinstance(workspace, Path), type(workspace)
        assert workspace.exists(), f"Workspace must exist: '{workspace}'."
        assert workspace.is_dir(), f"Workspace must be a path: '{workspace}'."

        result = [p for p in workspace.iterdir() if p.is_dir()]

        return result

    @staticmethod
    def erase(workspace: Path, name: str) -> None:
        """
        Erase the specified session in workspace.
        This erases all files and directories in the session.
        """

        assert isinstance(workspace, Path), type(workspace)
        assert workspace.exists(), f"Workspace must exist: '{workspace}'."

        assert isinstance(name, str), type(name)
        assert name.strip()

        path = Path((workspace) / name).resolve()
        assert path.exists(), f"Path must exist: '{path}'."
        assert path.is_dir(), f"Path must be a path: '{path}'."

        log.debug("Erase path '%s' ...", path)
        shutil.rmtree(path, ignore_errors=False)
        log.info("Erase path '%s' OK.", path)

        return

    @staticmethod
    def create(
        workspace: Path,
        name: str,
        characteristics: list[Iso25010],
        title: str,
    ) -> Session:
        """Create a new session with specified workspace and name."""

        assert isinstance(workspace, Path), type(workspace)
        assert workspace.exists(), f"Workspace must exist: '{workspace}'."

        assert isinstance(name, str), type(name)
        assert name.strip()

        assert isinstance(characteristics, list), type(characteristics)

        assert isinstance(title, str), type(title)
        assert title.strip()

        log.debug("Create session with id '%s' in '%s' ...", name, workspace)

        path = Path((workspace) / name).resolve()
        assert not path.exists(), f"Path must not exist: '{path}'."

        log.debug("Create path '%s' ...", path)
        path.mkdir()
        log.info("Create path '%s' OK.", path)

        source_doc = Path(path) / Constant.SOURCE_DOCUMENT
        assert (
            not source_doc.exists()
        ), f"Source document must not exist: '{source_doc}'."

        template = f"""// This is the text for the requirement set '{name}'.
// Title: {title}

# General Overview

{title}

"""

        log.debug(
            "Create document '%s' with [%s] ...",
            source_doc.name,
            [c.name for c in characteristics],
        )
        lines = template.splitlines()
        for c in characteristics:
            lines.append(f"# {c.value}\n")
        lines.append("")

        data = "\n".join(lines)
        source_doc.write_text(data, encoding="utf-8")

        log.info(
            "Create document '%s' with [%s] OK.",
            source_doc.name,
            [c.name for c in characteristics],
        )

        log.info(
            "Create session with id '%s' in '%s' OK ['%s'].",
            name,
            workspace,
            path,
        )

        return Session(workspace, name)
