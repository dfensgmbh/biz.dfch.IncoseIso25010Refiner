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

"""Integration tests for JiraClient.

These tests make REAL HTTP calls to the on-prem Jira instance.
They require a valid API token to be set in the environment variable
JIRA_API_TOKEN before running.

Run explicitly with:
    uv run python -m unittest tests.test_jira_client_integration -v

They are intentionally excluded from the default test discovery pattern
(test_*.py) so they do not run in CI or during normal unit test runs.
"""

import os
import unittest

from biz.dfch.incoseiso25010refiner.jira.jira_client import (
    JiraClient,
    JiraRequirementFields,
)

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://jira.example.com/jira")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "DEAD")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "dead-dead-dead-dead")


@unittest.skipIf(
    "true" == os.getenv("GITHUB_ACTIONS"),
    "Integration tests are excluded from GitHub Actions runners.",
)
@unittest.skipUnless(
    JIRA_API_TOKEN,
    "Integration tests require JIRA_API_TOKEN environment variable to be set.",
)
class TestJiraClientIntegration(unittest.TestCase):
    """Integration tests that exercise JiraClient against the real Jira
    instance.

    Each test that creates an issue cleans up after itself by deleting it in
    tearDown, so a failed assertion never leaves orphaned issues behind.
    """

    _created_issue_key: str | None

    def setUp(self):
        self.client = JiraClient(base_url=JIRA_BASE_URL, api_token=JIRA_API_TOKEN)
        self._created_issue_key = None

    def tearDown(self):
        if self._created_issue_key is not None:
            try:
                self.client.delete_issue(self._created_issue_key)
            except RuntimeError:
                pass  # Already deleted by the test itself, or not found.

    # ------------------------------------------------------------------
    # create_issue
    # ------------------------------------------------------------------

    def test_create_issue_returns_issue_key_with_correct_project_prefix(self):
        fields = JiraRequirementFields(
            project_key=JIRA_PROJECT_KEY,
            summary="[Integration test] The system shall respond within 200 ms.",
        )

        self._created_issue_key = self.client.create_issue(fields)

        self.assertTrue(
            self._created_issue_key.startswith(f"{JIRA_PROJECT_KEY}-"),
            f"Expected key starting with '{JIRA_PROJECT_KEY}-', got '{self._created_issue_key}'",
        )

    def test_create_issue_with_all_fields(self):
        fields = JiraRequirementFields(
            project_key=JIRA_PROJECT_KEY,
            summary="[Integration test] Full-field requirement.",
            description="Created by integration test.",
            labels=["integration-test"],
            category="Performance",
        )

        self._created_issue_key = self.client.create_issue(fields)

        self.assertIsNotNone(self._created_issue_key)
        self.assertGreater(len(self._created_issue_key), 0)

    # ------------------------------------------------------------------
    # edit_issue
    # ------------------------------------------------------------------

    def test_edit_issue_summary(self):
        fields = JiraRequirementFields(
            project_key=JIRA_PROJECT_KEY,
            summary="[Integration test] Original summary.",
        )
        self._created_issue_key = self.client.create_issue(fields)

        self.client.edit_issue(
            self._created_issue_key,
            summary="[Integration test] Updated summary.",
        )
        # No exception means the edit was accepted by Jira (HTTP 204).

    def test_edit_issue_all_fields(self):
        fields = JiraRequirementFields(
            project_key=JIRA_PROJECT_KEY,
            summary="[Integration test] Issue to be fully edited.",
        )
        self._created_issue_key = self.client.create_issue(fields)

        self.client.edit_issue(
            self._created_issue_key,
            summary="[Integration test] Edited summary.",
            description="Edited description.",
            labels=["integration-test", "edited"],
            category="Reliability",
        )
        # No exception means all fields were accepted by Jira (HTTP 204).

    def test_edit_issue_with_no_fields_does_not_raise(self):
        fields = JiraRequirementFields(
            project_key=JIRA_PROJECT_KEY,
            summary="[Integration test] Issue for no-op edit.",
        )
        self._created_issue_key = self.client.create_issue(fields)

        # Calling edit_issue with no fields must be a silent no-op.
        self.client.edit_issue(self._created_issue_key)

    # ------------------------------------------------------------------
    # delete_issue
    # ------------------------------------------------------------------

    def test_delete_issue_succeeds(self):
        fields = JiraRequirementFields(
            project_key=JIRA_PROJECT_KEY,
            summary="[Integration test] Issue to be deleted.",
        )
        issue_key = self.client.create_issue(fields)

        self.client.delete_issue(issue_key)

        # Mark as already deleted so tearDown does not attempt it again.
        self._created_issue_key = None

    def test_delete_nonexistent_issue_raises_runtime_error(self):
        with self.assertRaises(RuntimeError):
            self.client.delete_issue(f"{JIRA_PROJECT_KEY}-999999")

    # ------------------------------------------------------------------
    # Full lifecycle: create → edit → delete
    # ------------------------------------------------------------------

    def test_full_lifecycle(self):
        # 1. Create
        fields = JiraRequirementFields(
            project_key=JIRA_PROJECT_KEY,
            summary="[Integration test] Lifecycle requirement.",
            description="Initial description.",
            labels=["integration-test"],
            category="Performance",
        )
        issue_key = self.client.create_issue(fields)
        self.assertTrue(issue_key.startswith(f"{JIRA_PROJECT_KEY}-"))

        # 2. Edit
        self.client.edit_issue(
            issue_key,
            summary="[Integration test] Lifecycle requirement (revised).",
            description="Revised description.",
            labels=["integration-test", "revised"],
            category="Reliability",
        )

        # 3. Delete
        self.client.delete_issue(issue_key)

        # Mark as already deleted so tearDown does not attempt it again.
        self._created_issue_key = None


if __name__ == "__main__":
    unittest.main()
