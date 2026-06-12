# Copyright (C) 2025 - 2026 Ronald Rink, d-fens GmbH, http://d-fens.ch
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

"""Unit tests for JiraClient and JiraRequirementFields.

All HTTP calls are mocked via patch.object on the session.
No network access is required or performed.
"""

import unittest
from unittest.mock import MagicMock, patch

from biz.dfch.incoseiso25010refiner.jira.jira_client import (
    ISSUE_TYPE_REQUIREMENT,
    JiraClient,
    JiraRequirementFields,
)

API_TOKEN = "xyz"
PROJECT_KEY = "ABCD"
BASE_URL = "https://jira.example.com/jira"
ISSUE_KEY = "ABCD-1"


def make_response(status_code: int, json_data: dict | None = None) -> MagicMock:
    """Return a minimal mock of a requests.Response."""
    response = MagicMock()
    response.ok = status_code < 400
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.text = str(json_data or "")
    return response


class TestJiraRequirementFields(unittest.TestCase):
    """Tests for the JiraRequirementFields dataclass."""

    def test_required_fields_only(self):
        fields = JiraRequirementFields(
            project_key=PROJECT_KEY,
            summary="The system shall do something.",
        )

        self.assertEqual(fields.project_key, PROJECT_KEY)
        self.assertEqual(fields.summary, "The system shall do something.")
        self.assertIsNone(fields.description)
        self.assertEqual(fields.labels, [])
        self.assertIsNone(fields.category)

    def test_all_fields(self):
        fields = JiraRequirementFields(
            project_key=PROJECT_KEY,
            summary="The system shall do something.",
            description="Detailed description.",
            labels=["functional", "high-priority"],
            category="Performance",
        )

        self.assertEqual(fields.project_key, PROJECT_KEY)
        self.assertEqual(fields.summary, "The system shall do something.")
        self.assertEqual(fields.description, "Detailed description.")
        self.assertEqual(fields.labels, ["functional", "high-priority"])
        self.assertEqual(fields.category, "Performance")

    def test_labels_default_is_independent_per_instance(self):
        fields_a = JiraRequirementFields(project_key=PROJECT_KEY, summary="A")
        fields_b = JiraRequirementFields(project_key=PROJECT_KEY, summary="B")

        fields_a.labels.append("label-x")

        self.assertEqual(fields_a.labels, ["label-x"])
        self.assertEqual(fields_b.labels, [])


class TestJiraClientInit(unittest.TestCase):
    """Tests for JiraClient.__init__ via observable public behaviour."""

    def test_raises_on_empty_base_url(self):
        with self.assertRaises(AssertionError):
            JiraClient(base_url="", api_token=API_TOKEN)

    def test_raises_on_blank_base_url(self):
        with self.assertRaises(AssertionError):
            JiraClient(base_url="   ", api_token=API_TOKEN)

    def test_raises_on_empty_api_token(self):
        with self.assertRaises(AssertionError):
            JiraClient(base_url=BASE_URL, api_token="")

    def test_raises_on_blank_api_token(self):
        with self.assertRaises(AssertionError):
            JiraClient(base_url=BASE_URL, api_token="   ")

    def test_trailing_slash_in_base_url_does_not_produce_double_slash_in_request(
        self,
    ):
        client = JiraClient(base_url=BASE_URL + "/", api_token=API_TOKEN)
        fields = JiraRequirementFields(project_key=PROJECT_KEY, summary="S")

        with patch.object(
            client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            client.create_issue(fields)

        call_url = mock_post.call_args[0][0]
        self.assertNotIn("//rest", call_url)


class TestJiraClientCreateIssue(unittest.TestCase):
    """Unit tests for JiraClient.create_issue."""

    def setUp(self):
        self.client = JiraClient(base_url=BASE_URL, api_token=API_TOKEN)

    def test_returns_issue_key(self):
        fields = JiraRequirementFields(
            project_key=PROJECT_KEY,
            summary="The system shall process requests within 200 ms.",
        )

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            result = self.client.create_issue(fields)

        self.assertEqual(result, ISSUE_KEY)
        mock_post.assert_called_once()

    def test_posts_to_correct_url(self):
        fields = JiraRequirementFields(project_key=PROJECT_KEY, summary="S")

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            self.client.create_issue(fields)

        call_url = mock_post.call_args[0][0]
        self.assertEqual(call_url, f"{BASE_URL}/rest/api/2/issue")

    def test_sends_issue_type_requirement(self):
        fields = JiraRequirementFields(project_key=PROJECT_KEY, summary="S")

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            self.client.create_issue(fields)

        sent_payload = mock_post.call_args[1]["json"]
        self.assertEqual(
            sent_payload["fields"]["issuetype"]["name"], ISSUE_TYPE_REQUIREMENT
        )

    def test_sends_project_key(self):
        fields = JiraRequirementFields(project_key=PROJECT_KEY, summary="S")

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            self.client.create_issue(fields)

        sent_payload = mock_post.call_args[1]["json"]
        self.assertEqual(sent_payload["fields"]["project"]["key"], PROJECT_KEY)

    def test_sends_summary(self):
        fields = JiraRequirementFields(
            project_key=PROJECT_KEY,
            summary="The system shall respond within 200 ms.",
        )

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            self.client.create_issue(fields)

        sent_payload = mock_post.call_args[1]["json"]
        self.assertEqual(
            sent_payload["fields"]["summary"],
            "The system shall respond within 200 ms.",
        )

    def test_sends_description_when_provided(self):
        fields = JiraRequirementFields(
            project_key=PROJECT_KEY,
            summary="S",
            description="Detailed description.",
        )

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            self.client.create_issue(fields)

        sent_payload = mock_post.call_args[1]["json"]
        self.assertEqual(
            sent_payload["fields"]["description"], "Detailed description."
        )

    def test_omits_description_when_not_provided(self):
        fields = JiraRequirementFields(project_key=PROJECT_KEY, summary="S")

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            self.client.create_issue(fields)

        sent_payload = mock_post.call_args[1]["json"]
        self.assertNotIn("description", sent_payload["fields"])

    def test_sends_labels_when_provided(self):
        fields = JiraRequirementFields(
            project_key=PROJECT_KEY,
            summary="S",
            labels=["functional", "high-priority"],
        )

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            self.client.create_issue(fields)

        sent_payload = mock_post.call_args[1]["json"]
        self.assertEqual(
            sent_payload["fields"]["labels"], ["functional", "high-priority"]
        )

    def test_omits_labels_when_empty(self):
        fields = JiraRequirementFields(project_key=PROJECT_KEY, summary="S")

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            self.client.create_issue(fields)

        sent_payload = mock_post.call_args[1]["json"]
        self.assertNotIn("labels", sent_payload["fields"])

    def test_sends_category_when_provided(self):
        fields = JiraRequirementFields(
            project_key=PROJECT_KEY,
            summary="S",
            category="Performance",
        )

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            self.client.create_issue(fields)

        sent_payload = mock_post.call_args[1]["json"]
        self.assertEqual(
            sent_payload["fields"]["customfield_category"], "Performance"
        )

    def test_omits_category_when_not_provided(self):
        fields = JiraRequirementFields(project_key=PROJECT_KEY, summary="S")

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(201, {"key": ISSUE_KEY}),
        ) as mock_post:
            self.client.create_issue(fields)

        sent_payload = mock_post.call_args[1]["json"]
        self.assertNotIn("customfield_category", sent_payload["fields"])

    def test_raises_runtime_error_on_400(self):
        fields = JiraRequirementFields(project_key=PROJECT_KEY, summary="S")

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(400, {"errorMessages": ["Bad request"]}),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                self.client.create_issue(fields)

        self.assertIn("400", str(ctx.exception))

    def test_raises_runtime_error_on_401(self):
        fields = JiraRequirementFields(project_key=PROJECT_KEY, summary="S")

        with patch.object(
            self.client._session,
            "post",
            return_value=make_response(
                401, {"errorMessages": ["Unauthorized"]}
            ),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                self.client.create_issue(fields)

        self.assertIn("401", str(ctx.exception))

    def test_raises_assertion_error_on_wrong_argument_type(self):
        with self.assertRaises(AssertionError):
            self.client.create_issue("not-a-fields-object")  # type: ignore[arg-type]


class TestJiraClientEditIssue(unittest.TestCase):
    """Unit tests for JiraClient.edit_issue."""

    def setUp(self):
        self.client = JiraClient(base_url=BASE_URL, api_token=API_TOKEN)

    def test_puts_to_correct_url(self):
        with patch.object(
            self.client._session,
            "put",
            return_value=make_response(204),
        ) as mock_put:
            self.client.edit_issue(ISSUE_KEY, summary="Updated summary")

        call_url = mock_put.call_args[0][0]
        self.assertEqual(call_url, f"{BASE_URL}/rest/api/2/issue/{ISSUE_KEY}")

    def test_sends_only_summary_when_only_summary_provided(self):
        with patch.object(
            self.client._session,
            "put",
            return_value=make_response(204),
        ) as mock_put:
            self.client.edit_issue(ISSUE_KEY, summary="New title")

        sent_payload = mock_put.call_args[1]["json"]
        self.assertIn("summary", sent_payload["fields"])
        self.assertNotIn("description", sent_payload["fields"])
        self.assertNotIn("labels", sent_payload["fields"])
        self.assertNotIn("customfield_category", sent_payload["fields"])

    def test_sends_all_fields_when_all_provided(self):
        with patch.object(
            self.client._session,
            "put",
            return_value=make_response(204),
        ) as mock_put:
            self.client.edit_issue(
                ISSUE_KEY,
                summary="New title",
                description="New description",
                labels=["updated"],
                category="Reliability",
            )

        sent_payload = mock_put.call_args[1]["json"]
        self.assertEqual(sent_payload["fields"]["summary"], "New title")
        self.assertEqual(
            sent_payload["fields"]["description"], "New description"
        )
        self.assertEqual(sent_payload["fields"]["labels"], ["updated"])
        self.assertEqual(
            sent_payload["fields"]["customfield_category"], "Reliability"
        )

    def test_does_not_call_api_when_no_fields_provided(self):
        with patch.object(self.client._session, "put") as mock_put:
            self.client.edit_issue(ISSUE_KEY)

        mock_put.assert_not_called()

    def test_raises_runtime_error_on_404(self):
        with patch.object(
            self.client._session,
            "put",
            return_value=make_response(404),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                self.client.edit_issue(ISSUE_KEY, summary="X")

        self.assertIn("404", str(ctx.exception))

    def test_raises_assertion_error_on_empty_issue_key(self):
        with self.assertRaises(AssertionError):
            self.client.edit_issue("", summary="X")

    def test_raises_assertion_error_on_blank_issue_key(self):
        with self.assertRaises(AssertionError):
            self.client.edit_issue("   ", summary="X")


class TestJiraClientDeleteIssue(unittest.TestCase):
    """Unit tests for JiraClient.delete_issue."""

    def setUp(self):
        self.client = JiraClient(base_url=BASE_URL, api_token=API_TOKEN)

    def test_deletes_correct_url(self):
        with patch.object(
            self.client._session,
            "delete",
            return_value=make_response(204),
        ) as mock_delete:
            self.client.delete_issue(ISSUE_KEY)

        call_url = mock_delete.call_args[0][0]
        self.assertEqual(call_url, f"{BASE_URL}/rest/api/2/issue/{ISSUE_KEY}")

    def test_succeeds_on_204(self):
        with patch.object(
            self.client._session,
            "delete",
            return_value=make_response(204),
        ):
            self.client.delete_issue(ISSUE_KEY)

    def test_raises_runtime_error_on_404(self):
        with patch.object(
            self.client._session,
            "delete",
            return_value=make_response(404),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                self.client.delete_issue(ISSUE_KEY)

        self.assertIn("404", str(ctx.exception))

    def test_raises_runtime_error_on_403(self):
        with patch.object(
            self.client._session,
            "delete",
            return_value=make_response(403),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                self.client.delete_issue(ISSUE_KEY)

        self.assertIn("403", str(ctx.exception))

    def test_raises_assertion_error_on_empty_issue_key(self):
        with self.assertRaises(AssertionError):
            self.client.delete_issue("")

    def test_raises_assertion_error_on_blank_issue_key(self):
        with self.assertRaises(AssertionError):
            self.client.delete_issue("   ")


if __name__ == "__main__":
    unittest.main()
