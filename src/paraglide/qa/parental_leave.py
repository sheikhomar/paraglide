from pathlib import Path
from typing import Dict, Iterator, cast

from llama_index import ServiceContext, StorageContext
from llama_index.embeddings.cohereai import CohereEmbedding
from llama_index.indices.loading import load_index_from_storage
from llama_index.indices.vector_store import VectorStoreIndex
from llama_index.indices.vector_store.retrievers import VectorIndexRetriever
from llama_index.node_parser import SimpleNodeParser
from llama_index.response_synthesizers import ResponseMode, get_response_synthesizer
from pydantic import BaseModel, Field


class ParentalLeaveStatuteQuery(BaseModel):
    """Represents a query for the parental leave statute."""

    question: str = Field(description="The question to ask the parental leave statute.")
    """The question to ask the parental leave statute."""

    situational_context: Dict[str, str] = Field(default_factory=dict)
    """User's situational context as key-value pairs.

    The keys are the names of the situational context variables and the values are the
    values of the situational context variables. The names are descriptions like
    "arbejdsforhold" and "arbejdstimer" and the values are the actual values like
    "lønmodtager" and "37 timer om ugen".
    """


class ParentalLeaveStatuteQAEngine:
    """Represents a question-answering engine for the parental leave statute."""

    def __init__(self, index_dir: Path, cohere_api_key: str) -> None:
        embed_model = CohereEmbedding(
            cohere_api_key=cohere_api_key,
            model_name="embed-multilingual-v3.0",
            input_type="search_query",
        )

        node_parser: SimpleNodeParser = SimpleNodeParser.from_defaults(
            chunk_size=512,
            chunk_overlap=10,
        )

        self._service_context: ServiceContext = ServiceContext.from_defaults(
            llm=None,
            embed_model=embed_model,
            node_parser=node_parser,
        )

        base_index = load_index_from_storage(
            storage_context=StorageContext.from_defaults(persist_dir=str(index_dir)),
            service_context=self._service_context,
        )

        self._vector_index: VectorStoreIndex = cast(VectorStoreIndex, base_index)

        # Configure the response mode so the retriever only returns the nodes
        # without sending the retreived nodes to an LLM.
        # https://docs.llamaindex.ai/en/stable/module_guides/querying/response_synthesizers/root.html#configuring-the-response-mode
        response_synthesizer = get_response_synthesizer(
            response_mode=ResponseMode.NO_TEXT,
            service_context=self._service_context,
        )

        base_retriever = self._vector_index.as_retriever(
            service_context=self._service_context,
            response_synthesizer=response_synthesizer,
        )

        self._retriever: VectorIndexRetriever = cast(
            VectorIndexRetriever, base_retriever
        )

    def run(self, query: ParentalLeaveStatuteQuery) -> Iterator[str]:
        # prompt = self._build_prompt(query)
        yield "Jeg kigger først lige i barselsloven. Hæng på...\n\n"

        query_for_retriever = self._build_query_for_retriever(query=query)

        retrieved_nodes = self._retriever.retrieve(
            str_or_query_bundle=query_for_retriever,
        )

        yield "Jeg har fundet flg. afsnit som kunne indeholde svar på dit spørgsmål:\n\n"

        for source_node in retrieved_nodes:
            # source_text_fmt = source_node.node.get_content(metadata_mode=MetadataMode.ALL).strip()

            reference = source_node.node.metadata["Reference"]
            chapter_no = source_node.node.metadata["Kapitel nummer"]
            chapter_title = source_node.node.metadata["Kapitel overskrift"]
            is_paragraph = source_node.node.metadata.get("Type", "") == "Paragraf"

            yield f"**Kapitel {chapter_no}: {chapter_title}."

            if is_paragraph:
                yield f" Paragraf: {reference}"
            else:
                yield f" {reference}"
            yield "**\n\n"

            yield f"{source_node.node.get_content().strip()}\n\n"

        # yield "\nDanner et svar udfra ovenstående afsnit. Vent venligst..."

    def _build_prompt(self, query: ParentalLeaveStatuteQuery) -> str:
        """Build the prompt for the query."""
        prompt = query.question + "\n\n"
        for key, value in query.situational_context.items():
            prompt += f"{key}: {value}\n"
        return prompt

    def _build_query_for_retriever(self, query: ParentalLeaveStatuteQuery) -> str:
        """Build the query for the retriever.

        The query is the question with the situational context as a prefix.

        Args:
            query (ParentalLeaveStatuteQuery): The query.

        Returns:
            str: The query for the retriever.
        """

        question_with_context = ""

        if len(query.situational_context) > 0:
            question_with_context += "Min nuværende situtation er:\n"

            for key, value in query.situational_context.items():
                question_with_context += f" - {key}: {value}\n"

            question_with_context += "\n"

        question_with_context += "Mit spørgsmål er:\n"
        question_with_context += query.question

        return question_with_context
