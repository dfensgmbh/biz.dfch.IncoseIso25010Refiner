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

"""Shared command options."""

from .args import Annotated
from .args import ApiTokenOpt
from .args import BaseUriOpt
from .args import ModelOpt
from .args import SessionIdOpt
from .args import WorkspaceOpt
from .args import FileOpt
from .args import InputOpt
from .args import PromptOpt

from .commit import commit
from .init import init
from .erase import erase
from .list import list_
from .query import query
from .refine import refine
from .restore import restore
from .validate import validate

__all__ = [
    "Annotated",
    "ApiTokenOpt",
    "BaseUriOpt",
    "FileOpt",
    "InputOpt",
    "PromptOpt",
    "ModelOpt",
    "SessionIdOpt",
    "WorkspaceOpt",

    "commit",
    "erase",
    "init",
    "list_",
    "query",
    "refine",
    "restore",
    "validate",
]
