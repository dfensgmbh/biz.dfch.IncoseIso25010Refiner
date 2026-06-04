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

"""FileUtils class."""

from pathlib import Path
import shutil

from biz.dfch.diagnostics import Clock

from ..iso25010 import Iso25010
from ..parse.models import Question


class FileUtils:
    """FileUtils"""

    @staticmethod
    def make_copy(file: Path, infix: str | None = None) -> Path:
        """append_infix"""

        assert isinstance(file, Path), type(file)

        if infix is None:
            infix = f"---{Clock.now_file()}"
        assert isinstance(infix, str), type(str)

        new_file = FileUtils.append_infix(file, infix)

        shutil.copy2(file, str(new_file))

        return new_file

    @staticmethod
    def append_infix(file: Path, infix: str) -> Path:
        """append_infix"""

        assert isinstance(file, Path), type(file)
        assert isinstance(infix, str), type(infix)

        return file.with_stem(f"{file.stem}{infix}")

    @staticmethod
    def find_project_root(marker: str = "pyproject.toml") -> Path:
        """Walk up the directory tree until a marker file is found."""

        current = Path(__file__).resolve()
        for parent in [current, *current.parents]:
            if (parent / marker).exists():
                return parent
        raise FileNotFoundError(
            f"Could not find project root (looking for '{marker}')"
        )

    @staticmethod
    def update_source_doc(file: Path, questions: list[Question]) -> str:
        """
        Annotate a source document with review questions grouped by
        ISO 25010 characteristic.

        For each characteristic heading found in the file (a line starting
        with ``# <characteristic>``), the matching questions from *questions*
        are inserted immediately after that heading as block-quote lines
        (``> <question text>``).
        The scan runs from the bottom of the file upward so that inserting
        lines does not shift the indices of headings that have not yet been
        processed.

        Args:
            file: Path to an existing, readable text file.
            questions: List of 
                :class:`~biz.dfch.incoseiso25010refiner.parse.models.Question`
                objects whose ``characteristic`` and ``question`` attributes
                are used for matching and insertion.

        Returns:
            The full updated file content as a single string with
            ``\\n``-separated lines and a trailing newline.

        Raises:
            AssertionError: If *file* does not exist or is not a regular file,
                or if either argument is of the wrong type.
        """
        assert isinstance(file, Path), type(file)
        assert file.exists(), file
        assert file.is_file(), file
        assert isinstance(questions, list), type(questions)

        lines = file.read_text(encoding="utf-8").splitlines()

        # Move from end to start.
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]

            for characteristic in Iso25010:
                if line.startswith(f"# {characteristic}"):
                    new_lines = [""]
                    for q in [
                        q.question
                        for q in questions
                        if q.characteristic == characteristic
                    ]:
                        # new_lines.append(f"// {characteristic}")
                        new_lines.append(f"> {q}")
                        new_lines.append("")

                    for j, new_line in enumerate(new_lines):
                        lines.insert(i + 1 + j, new_line)
                    break

        lines.append("")
        result: str = "\n".join(lines)

        return result
