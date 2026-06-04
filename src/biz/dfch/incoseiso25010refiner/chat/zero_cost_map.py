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

"""ZeroCostMap: a LiteLLM model-cost dictionary that never raises KeyError."""


class ZeroCostMap(dict):
    """A dictionary that returns a default cost for any missing model."""

    DEFAULT_COST = {
        "max_tokens": 128000,
        "input_cost_per_token": 0.0,
        "output_cost_per_token": 0.0,
        "litellm_provider": "openai",
        "mode": "chat",
    }

    def __getitem__(self, key):
        return super().get(key, self.DEFAULT_COST)

    def get(self, key, default=None):
        _ = default
        return super().get(key, self.DEFAULT_COST)

    def __contains__(self, key):
        # Tell LiteLLM that we have cost information for every model.
        return True
