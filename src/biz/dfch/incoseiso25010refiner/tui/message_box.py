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

"""Reusable MessageBox modal screen."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from .message_box_result import MessageBoxResult


class MessageBox(ModalScreen[int]):
    """A reusable centered modal message box."""

    _ID_BUTTON_PREFIX = "id_button_"
    CSS_PATH = "message_box.css"

    BINDINGS = [("escape", "dismiss_cancel", "Cancel")]

    def __init__(
        self,
        *args,
        text: str,
        buttons: list[str],
        title: str | None = None,
        default_button: int = 0,
        **kwargs,
    ):
        """Initialise the MessageBox.

        Args:
            text: The message to display.
            buttons: List of button labels. The result is the index
                of the clicked button.
            title: Optional title shown above the message.
        """

        super().__init__(*args, **kwargs)

        assert isinstance(text, str), type(text)
        assert text.strip()
        assert isinstance(buttons, list), type(buttons)
        assert 0 <= default_button < len(buttons), f"default_button {default_button} out of range."

        self._text = text
        self._buttons = list(buttons)
        self._title = title
        self._default_button = default_button

    def compose(self) -> ComposeResult:
        """Compose the message box layout."""
        with Vertical(id="id_messagebox_dialog"):
            if self._title:
                yield Label(self._title, id="id_messagebox_title")
            yield Label(self._text, id="id_messagebox_text")
            with Horizontal(id="id_messagebox_buttons"):
                for i, label in enumerate(self._buttons):
                    variant = "primary" if i == self._default_button else "default"
                    yield Button(
                        str(label),
                        variant=variant,
                        id=f"{self._ID_BUTTON_PREFIX}{i}",
                    )

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss with the index of the pressed button."""
        button_id = event.button.id or ""
        if button_id.startswith(self._ID_BUTTON_PREFIX):
            index = int(button_id.removeprefix(self._ID_BUTTON_PREFIX))
            self.dismiss(index)

    def action_dismiss_cancel(self) -> None:
        """'<ESC>' returns '-1'."""
        self.dismiss(MessageBoxResult.ESCAPE)
