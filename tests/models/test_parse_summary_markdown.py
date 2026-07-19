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

# pylint: disable=C0114
# pylint: disable=C0115
# pylint: disable=C0116
# pylint: disable=C0301

"""Unit tests for parse_summary_markdown and Section."""

import unittest

from biz.dfch.incoseiso25010refiner.parse import Section, parse_summary_markdown

SAMPLE_TEXT = """# Zusammenfassung der Anforderungen für ABCD-1234
## Systemumfang
- Der Geldautomat muss Bargeldabhebungen unterstützen.
- Der Geldautomat darf nur Banknoten ausgeben.
## Kartenunterstützung
- Der Geldautomat muss VISA akzeptieren.
- Der Geldautomat darf AMEX nicht akzeptieren.
- Der Geldautomat muss den Kartentyp "GiroCard" unterstützen.
## Abhebungsregeln
- Der Geldautomat muss folgende Banknotenstückelungen zulassen: 10 CHF, 20 CHF, 50 CHF und 100 CHF.
- Der Geldautomat muss ein Tageslimit von 200 CHF pro Karte durchsetzen.
- Der Quelltext nennt 200 CHF auch als Mindestbetrag pro Transaktion.
## Sicherheit
- Der Geldautomat muss an einer Betonwand befestigt werden, um die physische Sicherheit des Benutzers bei der Bargeldabhebung zu gewährleisten.
## Fragen
- Definiert 200 CHF das Tagesmaximum, den Mindestbetrag pro Transaktion oder beides?
- Wie verhalten sich die reine VISA-Unterstützung und die "GiroCard"-Unterstützung zueinander?
"""  # noqa: E501


class TestSection(unittest.TestCase):
    """Tests for the Section dataclass."""

    def test_title_is_set(self):
        section = Section(title="Systemumfang")

        self.assertEqual(section.title, "Systemumfang")

    def test_description_defaults_to_empty_list(self):
        section = Section(title="Systemumfang")

        self.assertEqual(section.description, [])

    def test_description_is_set(self):
        section = Section(
            title="Systemumfang",
            description=["Der Geldautomat muss Bargeldabhebungen unterstützen."],
        )

        self.assertEqual(
            section.description,
            ["Der Geldautomat muss Bargeldabhebungen unterstützen."],
        )

    def test_description_default_is_independent_per_instance(self):
        section_a = Section(title="A")
        section_b = Section(title="B")

        section_a.description.append("item")

        self.assertEqual(section_a.description, ["item"])
        self.assertEqual(section_b.description, [])


class TestParseSummaryMarkdown(unittest.TestCase):
    """Tests for parse_summary_markdown."""

    def test_returns_list(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertIsInstance(result, list)

    def test_returns_correct_number_of_sections(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(len(result), 5)

    def test_all_items_are_sections(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        for item in result:
            self.assertIsInstance(item, Section)

    def test_first_section_title(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(result[0].title, "Systemumfang")

    def test_second_section_title(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(result[1].title, "Kartenunterstützung")

    def test_third_section_title(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(result[2].title, "Abhebungsregeln")

    def test_fourth_section_title(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(result[3].title, "Sicherheit")

    def test_fifth_section_title(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(result[4].title, "Fragen")

    def test_first_section_description_count(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(len(result[0].description), 2)

    def test_first_section_description_first_item(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(
            result[0].description[0],
            "Der Geldautomat muss Bargeldabhebungen unterstützen.",
        )

    def test_first_section_description_second_item(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(
            result[0].description[1],
            "Der Geldautomat darf nur Banknoten ausgeben.",
        )

    def test_second_section_description_count(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(len(result[1].description), 3)

    def test_third_section_description_count(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(len(result[2].description), 3)

    def test_fourth_section_description_count(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(len(result[3].description), 1)

    def test_fifth_section_description_count(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        self.assertEqual(len(result[4].description), 2)

    def test_bullet_prefix_is_stripped(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        for section in result:
            for item in section.description:
                self.assertFalse(item.startswith("- "))

    def test_h1_title_line_is_not_a_section(self):
        result = parse_summary_markdown(SAMPLE_TEXT)

        titles = [s.title for s in result]
        self.assertNotIn("Zusammenfassung der Anforderungen für ABCD-1234", titles)

    def test_empty_string_returns_empty_list(self):
        result = parse_summary_markdown("")

        self.assertEqual(result, [])

    def test_no_headings_returns_empty_list(self):
        text = "- some bullet\n- another bullet"

        result = parse_summary_markdown(text)

        self.assertEqual(result, [])

    def test_heading_with_no_bullets_has_empty_description(self):
        text = "## EmptySection\n\n## NextSection\n- item"

        result = parse_summary_markdown(text)

        self.assertEqual(result[0].title, "EmptySection")
        self.assertEqual(result[0].description, [])

    def test_bullets_before_any_heading_are_ignored(self):
        text = "- orphan bullet\n## Section\n- valid item"

        result = parse_summary_markdown(text)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].description, ["valid item"])

    def test_blank_lines_between_bullets_are_ignored(self):
        text = "## Section\n- first\n\n- second"

        result = parse_summary_markdown(text)

        self.assertEqual(result[0].description, ["first", "second"])

    def test_whitespace_is_stripped_from_titles(self):
        text = "##   Spaced Title   \n- item"

        result = parse_summary_markdown(text)

        self.assertEqual(result[0].title, "Spaced Title")

    def test_whitespace_is_stripped_from_bullet_items(self):
        text = "## Section\n-   leading and trailing   "

        result = parse_summary_markdown(text)

        self.assertEqual(result[0].description, ["leading and trailing"])


if __name__ == "__main__":
    unittest.main()
