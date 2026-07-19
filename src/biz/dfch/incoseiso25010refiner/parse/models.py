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

import difflib
import json
import re
from dataclasses import dataclass, field
from typing import TypeVar

T = TypeVar("T")


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
    classifications: list[Classification]


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
    scores: list[ScoreSummary]


@dataclass
class IsoResponse:
    phrase: str
    analysis: list[SentenceAnalysis]
    questions: list[Question]
    summary: Summary


@dataclass
class Section:
    title: str
    description: list[str] = field(default_factory=list)


def get_value(d: dict, key: str, return_type: type[T] = str) -> T:
    """Look up *key* in *d*, tolerating LLM typos in the actual key name.

    Resolution order:
    1. Exact match.
    2. Case-insensitive exact match.
    3. Closest match via difflib (cutoff 0.8).
    Raises KeyError when no sufficiently similar key is found.
    Raises TypeError when the resolved value is not an instance of
        *return_type*.
    """
    if key in d:
        value = d[key]
    else:
        lower_key = key.lower()
        for k in d:
            if k.lower() == lower_key:
                value = d[k]
                break
        else:
            matches = difflib.get_close_matches(key, d.keys(), n=1, cutoff=0.8)
            if not matches:
                raise KeyError(key)
            value = d[matches[0]]

    if not isinstance(value, return_type):
        raise TypeError(
            f"Expected '{return_type.__name__}' for key '{key}'. "
            f"Found '{type(value).__name__}'."
        )

    return value


def parse_summary_markdown(text: str) -> list[Section]:
    """Parse a markdown text into a list of Sections.

    Each Section has a 'title' (from a ## heading) and a 'description'
    (list of bullet point texts under that heading).
    """
    sections: list[Section] = []
    current: Section | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if re.match(r"^##\s+", line):
            current = Section(title=re.sub(r"^##\s+", "", line))
            sections.append(current)
        elif re.match(r"^-\s+", line) and current is not None:
            current.description.append(re.sub(r"^-\s+", "", line))

    return sections


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
                    characteristic=get_value(c, "characteristic"),
                    confidence=float(get_value(c, "confidence")),
                    rationale=get_value(c, "rationale"),
                )
                for c in item["classifications"]
            ],
        )
        for item in data["analysis"]
    ]

    # Parse questions
    questions = [
        Question(
            characteristic=get_value(q, "characteristic"),
            rationale=get_value(q, "rationale"),
            question=get_value(q, "question"),
        )
        for q in data["questions"]
    ]

    # Parse summary
    summary_data = data["summary"]
    summary = Summary(
        rationale=get_value(summary_data, "rationale"),
        scores=[
            ScoreSummary(
                characteristic=get_value(s, "characteristic"),
                score=float(get_value(s, "score")),
                rationale=get_value(s, "rationale"),
            )
            for s in get_value(summary_data, "scores", list)
        ],
    )

    return IsoResponse(
        phrase=data["phrase"],
        analysis=analysis,
        questions=questions,
        summary=summary,
    )
