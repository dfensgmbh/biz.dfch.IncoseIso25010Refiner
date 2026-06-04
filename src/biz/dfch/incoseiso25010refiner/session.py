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
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
import shutil

from biz.dfch.logging import log
from biz.dfch.diagnostics.clock import Clock

from .constant import Constant
from .iso25010 import Iso25010

from .text.text_utils import TextUtils
from .ui.rich_utils import RichUtils


@dataclass
class Question:
    """Represents a question with an optional answer."""

    question: str = ""
    idx: int = -1
    answer: list[str] = field(default_factory=list)
    start: int = -1
    end: int = -1

    def has_answer(self) -> bool:
        """Return `True` if question has an answer. Return `False` if not."""
        return 0 != len(self.answer)

    @staticmethod
    def is_question(line: str) -> bool:
        """Return `True` if the line is a question. Return  `False` if not."""
        return line.startswith(">")

    @staticmethod
    def is_terminator(line: str) -> bool:
        """Return `True` if the line ends a question. Return `False` if not."""
        assert isinstance(line, str), type(line)

        if line.startswith(">"):
            return True
        if line.startswith("//"):
            return True
        if line.startswith("#"):
            return True
        return False


class Session:
    """
    The session when you work with a requirement set.
    """

    class Source:
        """This is the source document of a `Session`."""

        _session: Session
        _name: str
        _file: Path

        def __init__(
            self, session: Session, name: str = Constant.SOURCE_DOCUMENT
        ) -> None:
            """
            Make a `Source` object in the specified `Session`.

            Args:
                session (Session): The `Session` from which to return the
                    source document.
                name (str): The name of the source document.

                    *default*: `source.md`.
            """

            assert isinstance(session, Session), type(session)
            assert isinstance(name, str), type(name)

            self._session = session
            self._name = name

            file = Path(session.path / name).resolve()
            assert file.exists(), f"Source document must exist: '{file}'."
            assert file.is_file(), f"Source must be a file: '{file}'."

            self._file = file

        @property
        def file(self) -> Path:
            """Return the source document file as `Path`."""
            return self._file

        @property
        def contents(self) -> str:
            """Return the contents of the source document of this session."""

            return self.file.read_text(encoding="utf-8")

        @staticmethod
        def _clean_document(lines: list[str]) -> list[str]:
            i = 0
            while i < len(lines):
                if (
                    lines[i].strip() == ""
                    and i + 1 < len(lines)
                    and lines[i + 1].strip() == ""
                    and i + 2 < len(lines)
                    and lines[i + 2].strip() == ""
                ):
                    lines.pop(i)
                else:
                    i += 1
            return lines

        @property
        def lines(self) -> list[str]:
            """Return the contents of the source document as a list of lines."""

            result = self.contents.splitlines()

            return result

        def update(
            self,
            value: str | list[str],
            *,
            do_not_clean: bool = False,
            do_add_version: bool = False,
        ) -> None:
            """Update the contents of the source document with `value`."""

            assert isinstance(value, (str, list)), type(value)
            assert isinstance(do_not_clean, bool), type(do_not_clean)
            assert isinstance(do_add_version, bool), type(do_add_version)

            log.debug("Update file '%s' ...", self.file)

            if isinstance(value, str):
                assert value.strip()
                value = value.splitlines()

            if not do_not_clean:
                value = self._clean_document(value)

            if do_add_version:
                self.add_version()

            value = "\n".join(value)
            value = value.rstrip("\n") + "\n"
            self.file.write_text(value, encoding="utf-8")
            log.info("Update file '%s' OK.", self.file)

        def get_versions(self) -> list[Path]:
            """
            Get a list of source document versions.
            The list contains the newest items first.
            """

            pattern = f"{self._file.stem}---*{self._file.suffix}"
            result = sorted(self._session.path.glob(pattern), reverse=True)

            return result

        def add_version(self) -> Path:
            """
            Add a new version of the source document to the session.

            You must set a checkpoint in the session, before you can start this
            function.
            """

            checkpoint = self._session.get_checkpoint()
            assert isinstance(checkpoint, datetime), (
                "You must create a checkpoint before you can start this "
                "function."
            )

            result = Path(
                self._session.path
                / (
                    f"{self.file.stem}---"
                    f"{Clock.format_file(checkpoint)}"
                    f"{self.file.suffix}"
                )
            ).resolve()

            # Create copy of source document.
            assert not result.exists(), f"File must not exist: '{result}'."

            log.debug("Make a copy of '%s' to '%s' ...", self.file, result)
            shutil.copy2(self._file, str(result))
            log.info("Make a copy of '%s' to '%s' OK.", self.file, result)

            assert result.exists(), f"File must exist: '{result}'."
            assert result.is_file(), f"File must be a file: '{result}'."

            return result

        def get_previous_version(self) -> Session.Source | None:
            """
            Return the previous version of the source document.

            Args:
                None (None): This method does not have any parameters.
            Returns:
                result (Session | None): An instance of a `Source` object that
                is the previous version the source document.

                When there is no previous version, the method returns `None`.
            """
            result: Session.Source | None = None

            versions = self.get_versions()
            if 0 == len(versions):
                return result

            previous = versions[0].name
            result = Session.Source(self._session, previous)

            return result

        def restore_previous_version(self) -> bool:
            """
            Restore the previous version of source document.

            Returns:
                result (bool): `True`, if operation is satisfactory.

                `False`, if not or if there is nothing to restore.
            """

            files = self.get_versions()
            if 0 == len(files):
                return False
            file = files[0]

            try:
                log.debug(f"Restore file: '{RichUtils.make_link(file)}' ...")
                # Delete file.
                self._file.unlink()
                # Rename copy to source file.
                file.rename(str(self._file))
                log.info(f"Restore file: '{RichUtils.make_link(file)}' OK.")

                return True
            except Exception as ex:  # pylint: disable=W0718
                log.error(
                    f"Restore file: '{RichUtils.make_link(file)}' OK.",
                    exc_info=ex,
                )

            return False

        def get_questions(self) -> list[Question]:
            """
            Return the list of questions and answers in the source document.
            """

            result: list[Question] = []

            lines = self.lines
            n = len(lines)
            i = 0

            while i < n:
                line = lines[i]
                if not Question.is_question(line):
                    i += 1
                    continue

                question = Question()
                question.question = line[1:].strip()
                question.idx = i

                result.append(question)

                i += 1
                while i < n:
                    line = lines[i]
                    if Question.is_terminator(line):
                        break
                    # Examine if there a 2 consecutive blank lines.
                    if (
                        line.strip() == ""
                        and i + 1 < n
                        and lines[i + 1].strip() == ""
                    ):
                        break

                    answer = line.strip()
                    if answer:
                        question.answer.append(answer)
                        if -1 == question.start:
                            question.start = i
                        question.end = i

                    i += 1

            return result

        def __repr__(self):
            return str(self._file)

        def __str__(self):
            return repr(self)

    CHECKPOINT_PATTERN = re.compile(
        r"---\d{4}-\d{2}-\d{2}---\d{2}-\d{2}-\d{2}$"
    )

    _workspace: Path
    _source: Source
    _checkpoint: datetime
    name: str
    path: Path

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

        self._checkpoint = self.set_checkpoint()
        self._workspace = workspace.resolve()
        self.name = name
        self.path = path
        self._source = self.Source(self)

    @property
    def source(self) -> Source:
        """Return the source document of this session."""

        return self._source

    def set_checkpoint(self) -> datetime:
        """
        Set a new checkpoint. If you set a checkpoint before,
        this function overwrites the checkpoint.
        """

        self._checkpoint = Clock().now()

        return self._checkpoint

    def get_checkpoint(self, style: bool | None = None) -> datetime | str:
        """
        Return the current session checkpoint, or create a new one
        if there is none.

        Args:
            style(bool | None):
                * If style is `None`, the return value is
                    `datetime`.
                * If style is `True`, the return value is
                    `yyyy-MM-dd---HH-mm-ss`.
                * If style is `True`, the return value is
                    `yyyy-MM-dd HH:mm:ss.fff`.

        Returns:
            result: (datetime | str):
                * If style is `None`, the return value is
                    `datetime`.
                * If style is `True`, the return value is
                    `yyyy-MM-dd---HH-mm-ss`.
                * If style is `True`, the return value is
                    `yyyy-MM-dd HH:mm:ss.fff`.
        """

        assert style is None or isinstance(style, bool), type(style)

        if self._checkpoint is None:
            self.set_checkpoint()

        if style is None:
            return self._checkpoint

        if style:
            return Clock.format_file(self._checkpoint)

        return Clock.format_isodate(self._checkpoint)

    def add_response(self, value: str) -> Path:
        """
        Add a new response with the current checkpoint to the session.
        """

        assert isinstance(value, str), type(value)
        assert isinstance(self._checkpoint, datetime), type(self._checkpoint)

        # Save response as json or text.
        is_json = TextUtils.is_json(value)
        if is_json:
            extension = Constant.RESPONSE_FILE_EXT
        else:
            extension = Constant.DEFAULT_FILE_EXT

        timestamp = Clock.format_file(self._checkpoint)
        result = (
            self.path / f"{Constant.RESPONSE_FILE_PREFIX}{timestamp}{extension}"
        ).resolve()

        log.debug("Writing response: '%s' ...", result)
        assert not result.exists(), result
        result.write_text(value, encoding="utf-8")
        log.info("Writing response: '%s' OK.", result)

        return result

    def get_items(self, base_name: str | None = None) -> list[Path]:
        """
        Return a list of item in this session that start with `base_name`.

        The result is a list with the newest element first.
        """

        assert base_name is None or isinstance(base_name, str), type(base_name)

        result: list[Path] = []

        if base_name is not None and not base_name.strip():
            base_name = None

        result = sorted(
            [
                f
                for f in self.path.iterdir()
                if f.is_file()
                and (base_name is None or f.stem.startswith(base_name))
                and self.CHECKPOINT_PATTERN.search(f.stem)
            ],
            reverse=True,
        )

        return result

    def add_item(self, base_name: str, value: str, suffix: str) -> Path:
        """
        Add an item to the current session. The item name has this format:
        `<base_name>---<checkpoint>`
        """

        assert isinstance(base_name, str), type(base_name)
        assert base_name.strip()
        assert isinstance(value, str), type(value)
        assert value.strip()
        assert isinstance(suffix, str), type(suffix)

        log.debug(f"Create file name from base '{base_name}' ...")
        name = f"{base_name}---{self.get_checkpoint(True)}{suffix}"
        file = Path(self.path / name).resolve()
        log.info(f"Create file name from base '{base_name}' OK: ['{file}'].")
        assert not file.exists(), f"File must not exist: '{file}'."

        log.debug(f"Write file '{file}' ...")
        file.write_text(value, encoding="utf-8")
        log.info(f"Write file '{file}' OK.")

        return file

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
