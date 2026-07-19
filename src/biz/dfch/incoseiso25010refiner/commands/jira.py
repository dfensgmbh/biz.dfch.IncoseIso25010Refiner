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

"""'jira' command."""

from pathlib import Path
from urllib.parse import quote

import typer
from dotenv import load_dotenv
from rich.console import Console

from biz.dfch.diagnostics import Stopwatch
from biz.dfch.i18n import LanguageCode
from biz.dfch.logging import log

from ..console import RichUtils
from ..info import Info
from ..iso25010 import Iso25010
from ..jira.jira_client import JiraClient, JiraRequirementFields
from ..parse import parse_summary_markdown
from ..session import Session
from .args import (
    CharacteristicsOpt,
    JiraApiTokenOpt,
    JiraBaseUriOpt,
    JiraProjectKeyOpt,
    LanguageOpt,
    SessionIdOpt,
    WorkspaceOpt,
)

load_dotenv()

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


@app.command()
def jira(
    uri: JiraBaseUriOpt,
    api_token: JiraApiTokenOpt,
    project: JiraProjectKeyOpt,
    session_id: SessionIdOpt,
    workspace: WorkspaceOpt = Path("."),
    characteristics: CharacteristicsOpt = None,
    language: LanguageOpt = LanguageCode.DEFAULT,
):
    """
    Make Jira issues from the summary of the requirements set.
    """

    assert isinstance(project, str), type(project)
    assert project.strip()

    assert isinstance(language, LanguageCode), type(language)

    if characteristics is None:
        characteristics = Iso25010.all()

    log.debug("Get session '%s' ...", session_id)
    session = Session(workspace, session_id)
    log.info("Get session '%s' OK.", session_id)

    items = session.get_items("summary", language=language)
    summary_file = items[0] if items else None
    assert summary_file is not None

    typer.echo(summary_file)

    data = {
        "workspace": RichUtils.make_link(workspace),
        "session_id": RichUtils.make_link(session.path, session_id),
        "language": language.name,
        "base_url": uri,
        "api_token": 0 < len(api_token),
        "project": project,
        "characteristics": characteristics,
        "summary": summary_file,
    }
    log.debug("Parameters: [%s]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console = Console()
    console.print(table)

    lines = summary_file.read_text(encoding="utf-8")
    sections = parse_summary_markdown(lines)

    # raise typer.Exit(0)

    log.debug("Create Jira client ...")
    client = JiraClient(base_url=uri, api_token=api_token)
    log.info("Create Jira client OK.")

    log.debug("Get current user ...")
    current_user = client.get_current_user()
    log.info("Get current user OK: '%s'.", current_user)

    log.debug("Create issues ...")
    sw = Stopwatch.start_new()
    first_issue_key: str | None = None

    try:
        for section in sections:
            fields = JiraRequirementFields(
                project_key=project,
                summary=section.title,
                description="\n".join(section.description) or None,
                source=session_id,
                characteristic="Functional",
                level="MUST",
                assignee=current_user,
            )
            log.debug("Create issue '%s' ...", section.title)
            issue_key = client.create_issue(fields)
            log.info("Create issue '%s' OK: '%s'.", section.title, issue_key)
            typer.echo(f"{issue_key}: {section.title}")
            if first_issue_key is None:
                first_issue_key = issue_key
        sw.stop()
    except TimeoutError as ex:
        sw.stop()
        elapsed = sw.elapsed_seconds
        log.error(
            "Create issues FAILED. TotalSeconds: %.3f",
            elapsed,
            exc_info=ex,
        )
        raise

    elapsed = sw.elapsed_seconds
    log.info("Create issues OK. TotalSeconds: %.3f", elapsed)

    jql = f'project = "{project}" AND issuetype = "Requirement" AND cf[14601] ~ "{session_id}"'
    search_url = f"{uri.rstrip('/')}/issues/?jql={quote(jql, safe='')}"

    log.info("Issues created. View them here: %s", search_url)
    log.info(
        "Issues created. View them here: %s",
        RichUtils.make_link(search_url, "Jira"),
    )
