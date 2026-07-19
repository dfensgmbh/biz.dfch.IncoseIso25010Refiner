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

"""prompt_builder — builds the system prompt for LLM queries."""

from __future__ import annotations

from biz.dfch.i18n import LanguageCode

from .constant import Constant
from .iso25010 import Iso25010


def get_prompt(
    template: str = Constant.PROMPT_REFINE,
    characteristics: list[Iso25010] | None = None,
    language: LanguageCode = LanguageCode.EN,
    questions: int = 5,
) -> str:
    """Build and return the system prompt string.

    Reads the prompt template from the prompts directory, optionally filters
    it to the requested ISO 25010 characteristics (preserving order and
    removing duplicates), and appends a language instruction when the target
    language is not English.

    Args:
        template:        Filename of the prompt template inside the prompts
                         directory. Defaults to ``Constant.PROMPT_REFINE``.
        characteristics: Ordered collection of ISO 25010 characteristics to
                         include. Duplicates are removed while preserving
                         the first occurrence order. When ``None`` or empty,
                         all characteristics are included.
        language:        Target language for the LLM output.
                         When not ``LanguageCode.EN``, a translation
                         instruction is appended to the prompt.

    Returns:
        The fully assembled system prompt as a string.
    """

    assert isinstance(template, str), type(template)
    assert template.strip(), "template must not be empty."
    assert characteristics is None or isinstance(characteristics, list), type(characteristics)
    assert isinstance(language, LanguageCode), type(language)
    assert isinstance(questions, int), type(questions)
    assert 0 < questions, questions

    template_file = Constant.PROMPTS_DIR / template
    assert template_file.exists(), f"Prompt template must exist: '{template_file}'."

    prompt = template_file.read_text(encoding="utf-8").replace(
        "{num_questions}",
        str(questions).replace("{remaining_questions}", str(questions - 1)),
    )

    # Normalise characteristics: deduplicate while preserving insertion order.
    if not characteristics:
        effective = list(Iso25010)
    else:
        effective = list(dict.fromkeys(characteristics))

    # When not all characteristics are requested, append an explicit
    # instruction so the LLM only covers the selected ones.
    all_characteristics = list(Iso25010)
    if effective != all_characteristics:
        names = ", ".join(f'"{c.value}"' for c in effective)
        prompt = (
            prompt
            + "\n\n"
            + "## Active Characteristics\n"
            + "Only analyse and generate questions for these characteristics: "
            + f"{names}.\n"
            + "Ignore all other ISO 25010 characteristics.\n"
        )

    # Append language instruction when output language is not English.
    if language != LanguageCode.EN:
        prompt = (
            prompt
            + "\n\n"
            + "## Output Language\n"
            + "Write all 'question', 'rationale', and 'analysis' fields "
            + f"in {language.value}. "
            + "All JSON keys must remain in English.\n"
        )

    return prompt
