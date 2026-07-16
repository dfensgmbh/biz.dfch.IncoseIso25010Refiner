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

"""Pydantic BaseModel versions of the ISO 25010 response models.

These are the canonical models used by the OpenAI provider path.
The legacy dataclass equivalents live in parse/models.py and will be
removed together with the legacy provider path.
"""

from __future__ import annotations

from pydantic import BaseModel


class Classification(BaseModel):
    """Classification of a sentence against an ISO 25010 characteristic."""

    characteristic: str
    confidence: float
    rationale: str


class SentenceAnalysis(BaseModel):
    """Analysis of a single sentence from the input phrase."""

    sentence_id: int
    line_number: int
    sentence: str
    classifications: list[Classification]


class Question(BaseModel):
    """A refinement question for a given ISO 25010 characteristic."""

    characteristic: str
    rationale: str
    question: str


class ScoreSummary(BaseModel):
    """Score and rationale for a single ISO 25010 characteristic."""

    characteristic: str
    score: float
    rationale: str


class Summary(BaseModel):
    """Overall summary of the ISO 25010 analysis."""

    rationale: str
    scores: list[ScoreSummary]


class IsoResponse(BaseModel):
    """Complete structured response from the LLM for ISO 25010 refinement."""

    phrase: str
    analysis: list[SentenceAnalysis]
    questions: list[Question]
    summary: Summary
