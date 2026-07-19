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

"""Reusable InputBox modal screen."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class InputBox(ModalScreen[str | None]):
    """A reusable centered modal input box with OK and Cancel buttons."""

    CSS_PATH = "input_box.css"

    BINDINGS = [("escape", "dismiss_cancel", "Cancel")]

    def __init__(
        self,
        *args,
        text: str,
        title: str | None = None,
        placeholder: str = "",
        initial_value: str = "",
        **kwargs,
    ):
        """Initialise the InputBox.

        Args:
            text: The prompt label to display above the input field.
            title: Optional title shown above the prompt.
            placeholder: Optional placeholder text for the input field.
            initial_value: Optional pre-filled value for the input field.
        """
        super().__init__(*args, **kwargs)

        assert isinstance(text, str), type(text)
        assert text.strip()

        self._text = text
        self._title = title
        self._placeholder = placeholder
        self._initial_value = initial_value

    def compose(self) -> ComposeResult:
        """Compose the input box layout."""
        with Vertical(id="id_inputbox_dialog"):
            if self._title:
                yield Label(self._title, id="id_inputbox_title")
            yield Label(self._text, id="id_inputbox_text")
            yield Input(
                value=self._initial_value,
                placeholder=self._placeholder,
                id="id_inputbox_input",
            )
            with Horizontal(id="id_inputbox_buttons"):
                yield Button("OK", variant="primary", id="id_inputbox_ok")
                yield Button("Cancel", variant="default", id="id_inputbox_cancel")

    def on_mount(self) -> None:
        """Focus the input field when the dialog opens."""
        self.query_one("#id_inputbox_input", Input).focus()

    @on(Button.Pressed, "#id_inputbox_ok")
    def on_ok(self, event: Button.Pressed) -> None:
        """Dismiss with the current input value."""
        value = self.query_one("#id_inputbox_input", Input).value
        self.dismiss(value)

    @on(Button.Pressed, "#id_inputbox_cancel")
    def on_cancel(self, event: Button.Pressed) -> None:
        """Dismiss with None when Cancel is pressed."""
        self.dismiss(None)

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Dismiss with the current input value when Enter is pressed."""
        self.dismiss(event.value)

    def action_dismiss_cancel(self) -> None:
        """Dismiss with None when Escape is pressed."""
        self.dismiss(None)
