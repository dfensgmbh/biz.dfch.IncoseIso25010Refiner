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

from dataclasses import dataclass
from typing import List
import json


@dataclass
class Classification:
    characteristic: str
    confidence: float
    rationale: str


@dataclass
class SentenceAnalysis:
    sentence_id: int
    line_number: int
    sentence: str
    classifications: List[Classification]


@dataclass
class Question:
    characteristic: str
    rationale: str
    question: str


@dataclass
class ScoreSummary:
    characteristic: str
    score: float
    rationale: str


@dataclass
class Summary:
    rationale: str
    scores: List[ScoreSummary]


@dataclass
class IsoResponse:
    phrase: str
    analysis: List[SentenceAnalysis]
    questions: List[Question]
    summary: Summary


def parse_iso_response(json_string: str) -> IsoResponse:
    """Convert JSON string to IsoResponse dataclass instance."""
    data = json.loads(json_string)

    # Parse analysis
    analysis = [
        SentenceAnalysis(
            sentence_id=item["sentence_id"],
            line_number=item["line_number"],
            sentence=item["sentence"],
            classifications=[
                Classification(
                    characteristic=c["characteristic"],
                    confidence=float(c["confidence"]),
                    rationale=c["rationale"],
                )
                for c in item["classifications"]
            ],
        )
        for item in data["analysis"]
    ]

    # Parse questions
    questions = [
        Question(
            characteristic=q["characteristic"],
            rationale=q["rationale"],
            question=q["question"],
        )
        for q in data["questions"]
    ]

    # Parse summary
    summary = Summary(
        rationale=data["summary"]["rationale"],
        scores=[
            ScoreSummary(
                characteristic=s["characteristic"],
                score=float(s["score"]),
                rationale=s["rationale"],
            )
            for s in data["summary"]["scores"]
        ],
    )

    return IsoResponse(
        phrase=data["phrase"],
        analysis=analysis,
        questions=questions,
        summary=summary,
    )
