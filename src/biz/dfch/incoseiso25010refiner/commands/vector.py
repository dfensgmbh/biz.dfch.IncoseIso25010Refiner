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

"""'vector' command."""

from dataclasses import asdict
from pathlib import Path
import uuid

from rich.console import Console
from rich.json import JSON
from rich.markdown import Markdown
from sentence_transformers import SentenceTransformer
import typer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from biz.dfch.asdste100vocab import Vocab
from biz.dfch.asdste100vocab import Word
from biz.dfch.asdste100vocab import WordNote
from biz.dfch.asdste100vocab import WordStatus

from biz.dfch.diagnostics import Stopwatch
from biz.dfch.logging import log

from ..chat.chat_client_factory import ChatClientFactory
from ..chat.chat_config import ChatConfig
from ..chat.providers import Providers
from ..info import Info
from ..text.text_utils import TextUtils
from ..console import RichUtils

from .args import ApiTokenOpt
from .args import BaseUriOpt
from .args import InputOpt
from .args import PromptOpt
from .args import MaxTokensOpt
from .args import ModelOpt
from .args import ProviderOpt
from .args import TemperateOpt
from .args import HfCacheOpt

app = typer.Typer(
    name=Info.name,
    help=Info.description,
    epilog=Info.epilog,
    no_args_is_help=True,
)


def index_vocabulary(
    words: list[Word],
    model: SentenceTransformer
) -> list[PointStruct]:
    result = []

    for idx, word in enumerate(words):
        # Generate the text representation.
        text_to_embed = get_embedding_string(word)

        # Generate embedding
        vector = model.encode(text_to_embed).tolist()

        # Create Point for Qdrant
        result.append(
            PointStruct(
                id=idx,  # Or use a UUID
                vector=vector,
                # Store the whole Word object as a dict in the payload
                # Use word.model_dump() if using Pydantic v2
                # payload=str(word),
                payload=asdict(word)
            )
        )

    return result


def get_embedding_string(word: Word) -> list[str]:
    """
    Concatenate important fields into a single string for semantic search.
    Note: We add the 'search_document: ' prefix required by Nomic v1.5.
    """

    assert isinstance(word, Word), type(word)

    nomic_prefix = "search_document: "

    result: list[str] = []

    log.debug(f"Operate word: '{word.name}' [{word.type_.name}] ...")

    if WordStatus.APPROVED == word.status:
        assert isinstance(word.meanings, list), type(word.meanings)
        assert 0 < len(word.meanings)

        for m in word.meanings:
            embedding = (
                f"{nomic_prefix} "
                f"Word '{word.name.lower()}' | "
                f"Meaning '{m.value}' | "
                f"Type '{word.type_.name}'"
            )
            result.append(embedding)
        return result

    if WordStatus.REJECTED == word.status:
        assert isinstance(word.alternatives, list), type(word.alternatives)

        if 0 == len(word.alternatives):
            assert isinstance(word.note, WordNote), type(word.note)
            assert isinstance(word.note.value, str), type(word.note.value)
            assert word.note.value.strip()
            embedding = (
                f"{nomic_prefix} "
                f"Word '{word.name.lower()} | "
                f"Note '{word.note.value}' | "
                f"Type '{word.type_.name}'"
            )
            result.append(embedding)
            return result

        for a in word.alternatives:
            embedding = (
                f"{nomic_prefix} "
                f"Word '{word.name.lower()} | "
                f"Alternative '{a.name.lower()}' ({a.type_.name}) | "
                f"Type '{word.type_.name}'"
            )
            result.append(embedding)
        return result

    raise ValueError(f"Word '{word.name}' has invalid status: '{word.status}'.")


@app.command()
def vector(
    api_token: ApiTokenOpt,
    text: InputOpt,
    hf_cache: HfCacheOpt,
    template: PromptOpt = "",
    uri: BaseUriOpt = "",
    model: ModelOpt = "",
    temperature: TemperateOpt = -1,
    max_tokens: MaxTokensOpt = -1,
    provider: ProviderOpt = Providers.DEFAULT,
):
    """
    Test with vector db Qdrant.
    """

    assert text.strip()
    assert isinstance(hf_cache, Path), type(hf_cache)

    input_file = Path(text)
    if input_file.exists() and input_file.is_file():
        text = input_file.read_text(encoding="utf-8")

    template_file = Path(template)
    if template_file.exists() and template_file.is_file():
        template = template_file.read_text(encoding="utf-8")

    if not uri.strip():
        uri = ChatConfig.default_values[provider].base_url

    if not model.strip():
        model = ChatConfig.default_values[provider].model

    data = {
        "provider": provider,
        "base_url": uri,
        "api_token": 0 < len(api_token),
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "input": text,
        "template": str(template_file),
    }
    log.debug("Parameters: [%s]", data)
    table = RichUtils.make_table(
        data,
        title="Parameters",
    )

    console = Console()
    console.print(table)

    embedding_model_name = "nomic-ai/nomic-embed-text-v1.5"
    embedding_model = SentenceTransformer(
        embedding_model_name,
        trust_remote_code=False,
    )

    COLLECTION_NAME = "asd-ste100"
    qdrant = QdrantClient(":memory:")
    qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )

    v = Vocab()
    points = index_vocabulary(list(v), embedding_model)
    # Batch upload to Qdrant
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Indexed {len(points)} words into Qdrant.")

    return

    # Prepare map for chat configuration.
    del data["input"]
    data["prompt"] = text
    data["api_token"] = api_token
    if -1 == max_tokens:
        del data["max_tokens"]
    if -1 == temperature:
        del data["temperature"]

    data["template_content"] = template
    data["session_id"] = str(uuid.uuid4())
    data["output_path"] = str(Path("."))

    # Prepare client.
    chat_config = ChatConfig.from_dict(data)
    client = ChatClientFactory.create(chat_config)

    # Start query.
    log.debug("Query LLM ...")
    sw = Stopwatch.start_new()
    try:
        response = client.query()
        sw.stop()
    except TimeoutError as ex:
        sw.stop()
        elapsed = sw.elapsed_seconds
        log.error(
            "Query LLM FAILED. TotalSeconds: %.3f",
            elapsed,
            exc_info=ex,
        )
        raise

    elapsed = sw.elapsed_seconds
    log.info("Query LLM OK. TotalSeconds: %.3f.", elapsed)

    # Examine response.
    text = TextUtils.remove_md_json(response)
    text = TextUtils.clean_pseudo_json(text)
    is_json = TextUtils.is_json(text)
    if not is_json:
        text = TextUtils.clean_text(text)
    is_json = TextUtils.is_json(text)

    log.info("Response:")
    try:
        console.print(JSON(text, indent=2))
    except Exception:  # pylint: disable=W0718  # type:ignore
        console.print(Markdown(text))
