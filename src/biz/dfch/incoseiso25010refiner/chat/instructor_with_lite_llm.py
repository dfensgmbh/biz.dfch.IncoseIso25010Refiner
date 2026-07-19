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

"""InstructorWithLiteLlm: generic structured-output chat client."""

import instructor

from .zero_cost_map import ZeroCostMap


class InstructorWithLiteLlm[T]:
    """
    A thin generic wrapper around instructor + LiteLLM that sends a
    structured chat completion and returns a validated Pydantic model T.

    Usage:
        client: InstructorWithLiteLlm[TranslationResponse] =
            InstructorWithLiteLlm(
                response_model=TranslationResponse,
                api_key="...",
                base_url="http://example.com:port",
                model="openai/model",
                system_prompt="You are a translator.",
                user_prompt="Translate this text.",
            )
        response, raw = client.complete()
    """

    _response_model: type[T]
    _api_key: str
    _base_url: str
    _model: str
    _system_prompt: str
    _user_prompt: str

    def __init__(  # noqa: PLR0913
        self,
        response_model: type[T],
        api_key: str,
        base_url: str,
        model: str,
        user_prompt: str,
        system_prompt: str = "",
    ) -> None:

        assert response_model is not None, type(response_model)

        assert isinstance(api_key, str), type(api_key)
        assert api_key.strip()

        assert isinstance(base_url, str), type(base_url)
        assert base_url.strip()

        assert isinstance(model, str), type(model)
        assert model.strip()

        assert isinstance(user_prompt, str), type(user_prompt)
        assert user_prompt.strip()
        assert isinstance(system_prompt, str), type(system_prompt)

        from litellm import litellm  # pylint: disable=C0415  # noqa: PLC0415

        litellm.model_cost = ZeroCostMap(litellm.model_cost)

        self._response_model = response_model
        self._api_key = api_key
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"
        self._base_url = base_url
        self._model = f"openai/{model}"
        self._system_prompt = system_prompt
        self._user_prompt = user_prompt

    def complete(self) -> tuple[T, object]:
        """
        Send the chat completion request and return a tuple of
        (parsed response model, raw LiteLLM response).
        """

        from litellm import completion  # pylint: disable=C0415  # noqa: PLC0415

        client = instructor.from_litellm(
            completion,
            mode=instructor.Mode.MD_JSON,
        )

        messages = []
        if self._system_prompt.strip():
            messages.append({"role": "system", "content": self._system_prompt})
        messages.append({"role": "user", "content": self._user_prompt})

        response, raw = client.create_with_completion(
            model=self._model,
            messages=messages,
            response_model=self._response_model,  # type: ignore
            api_key=self._api_key,
            base_url=self._base_url,
        )

        return response, raw
