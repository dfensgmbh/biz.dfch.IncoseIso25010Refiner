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

"""MessageBoxOk modal screen."""

from biz.dfch.incoseiso25010refiner.tui.message_box import MessageBox


class MessageBoxOk(MessageBox):
    """A MessageBox with a single OK button."""

    def __init__(
        self,
        *args,
        text: str,
        title: str | None = None,
        **kwargs,
    ):
        """Initialise with a single OK button."""
        buttons: list[str] = ["OK"]
        super().__init__(*args, text=text, buttons=buttons, title=title, **kwargs)
