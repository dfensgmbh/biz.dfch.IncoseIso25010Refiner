# Copyright (c) 2025-2026 Ronald Rink, http://d-fens.ch
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

"""ISO25010 characteristics."""

from enum import StrEnum
from dataclasses import dataclass


class Iso25010(StrEnum):
    """ISO25010 main characteristics."""

    FUNCTIONALITY = "functional suitability"
    PERFORMANCE = "performance	efficiency"
    COMPATIBILITY = "compatibility"
    INTERACTION = "interaction capability"
    RELIABILITY = "reliability"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    FLEXIBILITY = "flexibility"
    SAFETY = "safety"


class Iso25010Functionality(StrEnum):
    """ISO25010 characteristics and description of 'functional suitability'."""

    FUNCTIONAL_COMPLETENESS = "capability of a product to provide a set of functions that covers all the specified tasks and intended users’ objectives"
    FUNCTIONAL_CORRECTNESS = "capability of a product to provide accurate results when used by intended users"
    FUNCTIONAL_APPROPRIATENESS = "capability of a product to provide functions that facilitate the accomplishment of specified tasks and objectives"


@dataclass(frozen=True)
class Iso25010Characteristics:
    """ISO25010 characteristics."""

    FUNCTIONALITY = Iso25010Functionality  # pylint: disable=C0103
