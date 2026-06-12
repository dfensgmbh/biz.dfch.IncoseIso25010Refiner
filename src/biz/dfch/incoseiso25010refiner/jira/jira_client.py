# Copyright (c) 2026 Ronald Rink, http://d-fens.ch
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

"""Jira client for managing custom 'Requirement' issue types on an on-prem Jira instance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import requests

ISSUE_TYPE_REQUIREMENT = "Requirement"


@dataclass
class JiraRequirementFields:
    """Fields for a Jira 'Requirement' issue."""

    project_key: str
    summary: str
    description: Optional[str] = None
    labels: list[str] = field(default_factory=list)
    # 'category' is mapped to the Jira custom field 'customfield_category'.
    # Adjust the field name to match your on-prem Jira configuration.
    category: Optional[str] = None


class JiraClient:
    """
    Client for managing custom 'Requirement' issues on an on-prem Jira instance.

    Authentication uses Personal Access Tokens (PAT).

    Example usage:
        client = JiraClient(
            base_url="https://jira.example.com/jira",
            api_token="your-personal-access-token",
        )

        key = client.create_issue(JiraRequirementFields(
            project_key="MYPROJ",
            summary="The system shall ...",
            description="Detailed description.",
            labels=["functional", "high-priority"],
            category="Performance",
        ))

        client.edit_issue(key, summary="Updated summary", labels=["updated"])

        client.delete_issue(key)
    """

    _base_url: str
    _session: requests.Session

    def __init__(self, base_url: str, api_token: str) -> None:
        """
        Initialise the Jira client.

        Args:
            base_url(str): Root URL of the Jira instance,
                example: 'https://jira.example.com/jira'.
            api_token(str):  Personal Access Token for authentication.
        """

        assert isinstance(base_url, str), type(base_url)
        assert base_url.strip()
        assert isinstance(api_token, str), type(api_token)
        assert api_token.strip()

        self._base_url = base_url.rstrip("/")

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_issue(self, fields: JiraRequirementFields) -> str:
        """
        Create a new 'Requirement' issue.

        Args:
            fields: Populated :class:`JiraRequirementFields` instance.

        Returns:
            result (str): The issue key of the newly created issue
                (e.g. 'MYPROJ-42').

        Raises:
            ValueError:  If *fields* is not a :class:`JiraRequirementFields`.
            RuntimeError: If the Jira API returns a non-success status code.
        """

        assert isinstance(fields, JiraRequirementFields), type(fields)

        payload = self._build_create_payload(fields)
        url = self._api_url("issue")

        response = self._session.post(url, json=payload)
        self._raise_for_status(response, "create issue")

        issue_key: str = response.json()["key"]
        return issue_key

    def edit_issue(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        labels: Optional[list[str]] = None,
        category: Optional[str] = None,
    ) -> None:
        """
        Edit an existing 'Requirement' issue identified by *issue_key*.

        Only the fields that are explicitly provided (i.e. not ``None``) are
        updated; all other fields remain unchanged.

        Args:
            issue_key:   Jira issue key, e.g. ``'MYPROJ-42'``.
            summary:     New summary / title.
            description: New description text.
            labels:      Replacement list of labels (replaces existing labels).
            category:    New category value.

        Raises:
            ValueError:   If *issue_key* is empty.
            RuntimeError: If the Jira API returns a non-success status code.
        """

        assert (
            isinstance(issue_key, str) and issue_key.strip()
        ), "issue_key must be a non-empty string."

        payload = self._build_edit_payload(
            summary=summary,
            description=description,
            labels=labels,
            category=category,
        )

        if not payload["fields"]:
            return

        url = self._api_url(f"issue/{issue_key}")
        response = self._session.put(url, json=payload)
        self._raise_for_status(response, f"edit issue '{issue_key}'")

    def delete_issue(self, issue_key: str) -> None:
        """
        Permanently delete an issue identified by *issue_key*.

        Args:
            issue_key: Jira issue key, e.g. ``'MYPROJ-42'``.

        Raises:
            ValueError:   If *issue_key* is empty.
            RuntimeError: If the Jira API returns a non-success status code.
        """

        assert (
            isinstance(issue_key, str) and issue_key.strip()
        ), "issue_key must be a non-empty string."

        url = self._api_url(f"issue/{issue_key}")
        response = self._session.delete(url)
        self._raise_for_status(response, f"delete issue '{issue_key}'")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _api_url(self, path: str) -> str:
        """Build a full REST API v2 URL for the given *path*."""
        return f"{self._base_url}/rest/api/2/{path.lstrip('/')}"

    def _build_create_payload(self, fields: JiraRequirementFields) -> dict:
        """Assemble the JSON payload for issue creation."""

        payload: dict = {
            "fields": {
                "project": {"key": fields.project_key},
                "summary": fields.summary,
                "issuetype": {"name": ISSUE_TYPE_REQUIREMENT},
            }
        }

        if fields.description is not None:
            payload["fields"]["description"] = fields.description

        if fields.labels:
            payload["fields"]["labels"] = fields.labels

        if fields.category is not None:
            # Adjust 'customfield_category' to the actual field ID used in
            # your on-prem Jira instance (check via /rest/api/2/field).
            payload["fields"]["customfield_category"] = fields.category

        return payload

    def _build_edit_payload(
        self,
        summary: Optional[str],
        description: Optional[str],
        labels: Optional[list[str]],
        category: Optional[str],
    ) -> dict:
        """Assemble the JSON payload for issue updates (only changed fields)."""

        updated_fields: dict = {}

        if summary is not None:
            updated_fields["summary"] = summary

        if description is not None:
            updated_fields["description"] = description

        if labels is not None:
            updated_fields["labels"] = labels

        if category is not None:
            # Adjust 'customfield_category' to the actual field ID used in
            # your on-prem Jira instance (check via /rest/api/2/field).
            updated_fields["customfield_category"] = category

        return {"fields": updated_fields}

    @staticmethod
    def _raise_for_status(response: requests.Response, operation: str) -> None:
        """Raise a :class:`RuntimeError` with details when the response indicates failure."""

        if response.ok:
            return

        raise RuntimeError(
            f"Jira API error during '{operation}': "
            f"HTTP {response.status_code} – {response.text}"
        )
