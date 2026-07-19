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

# flake8: noqa=E501
# pylint: disable=C0103
# pylint: disable=C0301

"""Requirement dataclass with JSON serialisation support."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from biz.dfch.incoseiso25010refiner.iso25010 import Iso25010
from biz.dfch.incoseiso25010refiner.parse.requirement_status import (
    RequirementStatus,
)


def _new_uuid() -> str:
    """Return a new UUID4 string."""
    return str(uuid.uuid4())


@dataclass
class Requirement:
    """A single requirement with ISO 25010 quality characteristics."""

    id: str = field(default_factory=_new_uuid)
    name: str = ""
    description: str = ""
    rationale: str = ""
    consequences: str = ""
    characteristics: list[Iso25010] = field(default_factory=list)
    status: RequirementStatus = RequirementStatus.DRAFT

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rationale": self.rationale,
            "consequences": self.consequences,
            "characteristics": [c.value for c in self.characteristics],
            "status": self.status.value,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Requirement:
        """Construct a Requirement from a dictionary (e.g. parsed from JSON)."""
        return Requirement(
            id=data.get("id", _new_uuid()),
            name=data.get("name", ""),
            description=data.get("description", ""),
            rationale=data.get("rationale", ""),
            consequences=data.get("consequences", ""),
            characteristics=[Iso25010(c) for c in data.get("characteristics", [])],
            status=RequirementStatus(data.get("status", RequirementStatus.DRAFT)),
        )
