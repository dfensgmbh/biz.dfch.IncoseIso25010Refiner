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

"""Textual TUI application."""

import contextlib
import io
from pathlib import Path

from textual.app import App, ComposeResult, SystemCommand
from textual import on
from textual.binding import Binding
from textual.widgets import (
    Footer,
    Header,
    Label,
    Button,
    Log,
    Static,
    Link,
    ListView,
    ListItem,
)
from textual.containers import Horizontal, Vertical

from ..commands.list import app as list_app
from ..commands.refine import app as refine_app
from ..commands.resolve import app as resolve_app
from ..commands.restore import app as restore_app
from ..info import Info
from ..session import Session
from .input_box import InputBox
from .message_box_ok import MessageBoxOk
from .message_box_ok_cancel import MessageBoxOkCancel
from .message_box import (
    MessageBox,
    MessageBoxResult,
)


class Container(Static):
    """Displays session metadata and actions."""

    _session: Session

    def __init__(self, session: Session, *args, **kwargs):
        """Initialise with the current session."""
        super().__init__(*args, **kwargs)
        self._session = session

    async def on_mount(self) -> None:
        """Populate the items list when the widget is mounted."""
        await self._refresh_items()

    async def _refresh_items(self) -> None:
        """Reload session items into the ListView."""
        list_view = self.query_one("#id_items", ListView)
        await list_view.clear()
        for item in self._session.get_items():
            await list_view.append(
                ListItem(
                    Link(item.name, url=f"file://{item}"),
                    id=f"item_{item.stem}",
                )
            )

    async def refresh_session(self) -> None:
        """Refresh the session metadata links and items list."""

        workspace_link = self.query_one("#id_workspace", Link)
        workspace_link.text = f"{self._session.workspace}"
        workspace_link.url = f"file://{self._session.workspace}"

        name_link = self.query_one("#id_name", Link)
        name_link.text = f"{self._session.name}"
        name_link.url = f"file://{self._session.workspace / self._session.name}"

        source_link = self.query_one("#id_source", Link)
        source_link.text = f"{self._session.source.file}"
        source_link.url = f"file://{self._session.source.file}"

        await self._refresh_items()

    def _run_app(self, app, args: list[str]) -> None:
        """Run a Typer app in a thread and stream output to the Log widget."""
        log = self.query_one("#id_log", Log)
        log.clear()

        def stream() -> None:
            class LogWriter(io.TextIOBase):
                """
                Writes log messages from external programs into
                our log window.
                """
                def __init__(self, callback):
                    self._callback = callback

                def write(self, text: str) -> int:
                    for line in text.splitlines():
                        if line:
                            self._callback(line)
                    return len(text)

            writer = LogWriter(
                lambda line: self.app.call_from_thread(log.write_line, line)
            )
            try:
                with (
                    contextlib.redirect_stdout(writer),
                    contextlib.redirect_stderr(writer),
                ):
                    app(args, standalone_mode=False)
                self.app.call_from_thread(
                    self.app.run_worker, self.refresh_session, thread=False
                )
            except Exception as ex:  # pylint: disable=W0718
                _ex = ex
                self.app.call_from_thread(
                    lambda: self.notify(
                        str(_ex), title="Command FAILED.", severity="error"
                    )
                )

        self.run_worker(stream, thread=True)

    def run_resolve(self) -> None:
        """
        Run the resolve function in a thread and stream output to the
        Log widget.
        """
        self._run_app(
            resolve_app,
            [
                "--workspace",
                str(self._session.workspace),
                "--session-id",
                str(self._session.name),
            ],
        )

    def run_refine(self) -> None:
        """
        Run the refine function in a thread and stream output to the Log widget.
        """
        self._run_app(
            refine_app,
            [
                "--workspace",
                str(self._session.workspace),
                "--session-id",
                str(self._session.name),
            ],
        )

    def run_restore(self) -> None:
        """
        Run the restore function in a thread and stream output to the
        Log widget.
        """
        self._run_app(
            restore_app,
            [
                "--workspace",
                str(self._session.workspace),
                "--session-id",
                str(self._session.name),
                "--yes",
            ],
        )

    @on(ListView.Highlighted)
    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """
        Refresh app bindings when the highlighted item changes.
        """
        _ = event
        self.app.refresh_bindings()

    def action_open_item(self) -> None:
        """
        Open the currently highlighted item file in the default application.
        """
        list_view = self.query_one("#id_items", ListView)
        highlighted = list_view.highlighted_child
        if highlighted is None:
            return
        for item in self._session.get_items():
            if f"item_{item.stem}" == highlighted.id:
                highlighted.query_one(Link).action_open_link()
                break

    def action_delete_item(self) -> None:
        """Delete the currently selected item file, with confirmation."""
        list_view = self.query_one("#id_items", ListView)
        highlighted = list_view.highlighted_child
        if highlighted is None:
            self.app.push_screen(
                MessageBoxOk(
                    text="You must select an item.",
                    title="Delete Item",
                )
            )
            return

        item_id = highlighted.id
        matched = [
            item
            for item in self._session.get_items()
            if f"item_{item.stem}" == item_id
        ]
        if not matched:
            return

        file = matched[0]

        def on_confirm(result: MessageBoxResult) -> None:
            if result == MessageBoxResult.OK:
                file.unlink()
                self.app.run_worker(self.refresh_session, thread=False)

        msg_box: MessageBox = MessageBoxOkCancel(
            text=f"Delete item: '{file.name}'?",
            title="Delete Item",
        )
        self.app.push_screen(
            msg_box,
            callback=on_confirm,  # type: ignore
        )  # type: ignore

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Trigger the source Link when the button is pressed."""
        if event.button.id == "id_button_edit":
            self.query_one("#id_source", Link).action_open_link()
            return

        if event.button.id == "id_button_resolve":
            self.run_resolve()
            return

        if event.button.id == "id_button_refine":
            self.run_refine()
            return

    def compose(self) -> ComposeResult:
        """Compose the session metadata rows and action button."""
        with Horizontal(id="id_workspace_row"):
            yield Link(
                "Workspace",
                url=f"file://{self._session.workspace}",
                tooltip=f"{self._session.workspace}",
                id="id_workspace",
            )
            yield Link(
                f"{self._session.name}",
                url=f"file://{self._session.workspace / self._session.name}",
                tooltip=f"{self._session.workspace / self._session.name}",
                id="id_name",
            )
            yield Link(
                f"{self._session.source.file}",
                url=f"{self._session.source.file}",
                tooltip=f"{self._session.source.file}",
                id="id_source",
            )
        with Horizontal(id="id_Loop"):
            yield Button("Edit", id="id_button_edit")
            yield Button("Resolve", id="id_button_resolve")
            yield Button("Refine", id="id_button_refine")
        with Vertical(id="id_Files"):
            yield Label("Items")
            yield ListView(id="id_items")
            yield Label("Output")
            yield Log(id="id_log", auto_scroll=True)


class Tui(App):
    """Main Textual TUI application."""

    TITLE = "INCOSE / ISO 25010 Refiner"
    SUB_TITLE = ""
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "show_about", "About"),
        Binding("e", "edit", "Edit", show=True),
        Binding("s", "resolve", "Resolve", show=True),
        Binding("f", "refine", "Refine", show=True),
        Binding("o", "open_item", "Open", show=True),
        Binding("d", "delete_item", "Delete", show=True),
        Binding("c", "clear_log", "Clear", show=True),
    ]
    CSS_PATH = "tui.css"

    _session: Session

    def __init__(self, workspace: Path, session_id: str, *args, **kwargs):
        """Initialise the TUI with the given workspace path and session ID."""
        super().__init__(*args, **kwargs)

        self.workspace = workspace
        self.session_id = session_id

        assert isinstance(workspace, Path), type(workspace)
        assert workspace.exists(), f"Workspace must exist: '{workspace}'."
        assert workspace.is_dir(), f"Workspace must be a path: '{workspace}'."

        path = Path((workspace) / session_id).resolve()
        assert path.exists(), f"Path must exist: '{path}'."
        assert path.is_dir(), f"Path must be a path: '{path}'."

        self._session = Session(workspace, session_id)

    def action_edit(self) -> None:
        """Trigger the 'Edit' button action."""
        self.query_one("#id_button_edit", Button).press()

    def action_resolve(self) -> None:
        """Trigger the 'Resolve' button action."""
        self.query_one("#id_button_resolve", Button).press()

    def action_refine(self) -> None:
        """Trigger the 'Refine' button action."""
        self.query_one("#id_button_refine", Button).press()

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        """
        Show open_item and delete_item in the footer only when an item
        is highlighted.
        """
        if action in ("open_item", "delete_item"):
            try:
                list_view = self.query_one("#id_items", ListView)
                return list_view.highlighted_child is not None
            except Exception:  # pylint: disable=W0718
                return False
        return True

    def action_open_item(self) -> None:
        """Trigger the open item action."""
        self.query_one(Container).action_open_item()

    def action_delete_item(self) -> None:
        """Trigger the delete item action."""
        self.query_one(Container).action_delete_item()

    def action_clear_log(self) -> None:
        """Clear the log output."""
        self.query_one("#id_log", Log).clear()

    def action_show_about(self) -> None:
        """Push the About modal screen."""
        screen: MessageBoxOk = MessageBoxOk(
            text=f"{Info.description}\n\n{Info.epilog}",
            title="About",
        )
        self.push_screen(screen)

    def get_system_commands(self, screen):
        """Add custom commands to the command palette."""
        yield from super().get_system_commands(screen)
        yield SystemCommand(
            "Select Session",
            "Select an existing 'requirement set'.",
            self._refresh_session,
        )
        yield SystemCommand(
            "Custom Command",
            "Show the 'Custom Command' dialog",
            self._show_custom_command,
        )
        yield SystemCommand(
            "Restore",
            "Restore the previous version of the source document",
            self._restore,
        )
        yield SystemCommand(
            "List Sessions",
            "Show all sessions in the workspace",
            self._list_sessions,
        )

    def _refresh_session(self) -> None:
        """Trigger a session refresh from the command palette."""

        title = "Select Session"

        def on_result(value: str | None) -> None:
            if value is None or not value.strip():
                self.call_after_refresh(
                    lambda: self.notify(
                        "No new session selected.",
                        title=title,
                        severity="warning",
                    )
                )
                return

            try:
                self.call_after_refresh(
                    lambda: self.notify(
                        f"Load new session: '{value}' ...", title=title
                    )
                )
                self._session = Session(self._session.workspace, value)
            except Exception as ex:  # pylint: disable=W0718
                error = "Cannot get session"
                self.push_screen(MessageBoxOk(text=str(ex), title=error))
                self.call_after_refresh(
                    lambda: self.notify(
                        f"Load new session: '{value}' FAILED.",
                        title=title,
                        severity="error",
                    )
                )
                return

            self.call_after_refresh(
                lambda: self.notify(
                    f"Load new session: '{value}' OK.", title=title
                )
            )
            container = self.query_one(Container)
            container._session = self._session
            self.run_worker(container.refresh_session, thread=False)

        self.push_screen(
            InputBox(
                text="Type in the name of the session.",
                title=title,
            ),
            callback=on_result,
        )

    def _list_sessions(self) -> None:
        """Invoke the list command from the command palette."""
        self.query_one(Container)._run_app(
            list_app,
            [
                "--workspace",
                str(self._session.workspace),
            ],
        )

    def _restore(self) -> None:
        """Trigger restore from the command palette."""

        def on_confirm(result: int) -> None:
            if result == MessageBoxResult.OK:
                self.query_one(Container).run_restore()

        self.push_screen(
            MessageBoxOkCancel(
                text="Restore the previous version of the source document?",
                title="Restore",
            ),
            callback=on_confirm,  # type: ignore
        )  # type: ignore

    def _show_custom_command(self) -> None:
        """Push the "Custom Command" modal screen."""
        msg_Box = (
            MessageBoxOkCancel(
                text="Custom Command Text",
                title="Custom Command Title",
            ),
        )
        self.push_screen(
            msg_Box,  # type: ignore
            callback=self._on_custom_command_result,  # type: ignore
        )  # type: ignore

    def _on_custom_command_result(self, result: MessageBoxResult) -> None:
        """Handle the result of the "Custom Command" modal."""
        if result == MessageBoxResult.OK:
            self.notify("OK was pressed.")
        else:
            self.notify("Cancel was pressed.")

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header(icon="R", show_clock=True)
        yield Container(self._session)
        yield Footer()
