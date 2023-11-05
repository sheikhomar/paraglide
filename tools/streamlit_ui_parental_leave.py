import os
from pathlib import Path
from typing import Iterator, Optional, cast

import streamlit as st
from paraglide.data.models import ChatConversation, ChatMessageRole
from paraglide.qa.parental_leave import (
    ParentalLeaveStatuteQAEngine,
    ParentalLeaveStatuteQuery,
)
from streamlit.delta_generator import DeltaGenerator

WORK_SITUATION_OPTIONS = [
    "lønmodtager",
    "selvstændig",
    "ledig",
    "studerende",
    "søfarende",
]

WORK_SITUATION_OPTION_OTHER = "anden"

INITIAL_QUESTIONS = [
    "Hvor mange ugers barsel har jeg ret til?",
    "Kan jeg få barselsdagpenge?",
]

WELCOME_TEXT = """Hej 👋

Jeg er Lærbar.

Jeg er kan hjælpe dig med at forstå barselsloven.
Skriv dit spørgsmål eller forespørgsel i chatten
nedenunder, så vil jeg forsøge at svare dig.
"""


def clean_user_input(input: Optional[str]) -> str:
    """Clean the user input."""
    if input is not None:
        return input.strip()
    return ""


class StreamlitApp:
    def __init__(self, qa_engine: ParentalLeaveStatuteQAEngine) -> None:
        """Initialize the app settings, if any."""
        self._qa_engine = qa_engine
        self._field_work_situation_val: Optional[str] = None

    def run(self) -> None:
        """Run the main app loop."""
        self._setup_page_config()
        self._build_main_content()

    @property
    def user_situation(self) -> str:
        """Return the user input from the situation field."""
        return clean_user_input(self._field_work_situation_val)

    @property
    def user_work_situation(self) -> str:
        """Return the user input from the situation field."""
        return clean_user_input(self._field_work_situation_val)

    @property
    def current_conversation(self) -> ChatConversation:
        """Return the current conversation."""

        current_conversation = cast(
            ChatConversation, st.session_state.get("current_conversation")
        )

        if current_conversation is None:
            current_conversation = self._create_conversation()
            st.session_state.current_conversation = current_conversation

        return current_conversation

    def _create_conversation(self) -> ChatConversation:
        """Create a new conversation with initial messages.

        Returns:
            ChatConversation: the new conversation.
        """
        conversation = ChatConversation()
        conversation.add_assistant_message(text=WELCOME_TEXT)
        return conversation

    def _setup_page_config(self) -> None:
        """Set up any app settings, if any."""
        st.set_page_config(
            page_title="Lærbar: Din guide til barselsloven",
            page_icon="👶",
            layout="wide",
            initial_sidebar_state="expanded",
        )

    def _build_main_content(self) -> None:
        """Build the main content of the app."""
        st.header("Lærbar: Din guide til barselsloven", anchor=False)

        self._build_input_pane(container=st.sidebar)
        self._build_content()

    def _build_input_pane(self, container: DeltaGenerator) -> None:
        """Build the navigation sidebar."""
        container.markdown("**Hvad er din situation?**")

        self._field_work_situation_val = container.selectbox(
            label="Din arbejdssituation",
            options=WORK_SITUATION_OPTIONS + [WORK_SITUATION_OPTION_OTHER],
        )
        if self._field_work_situation_val == WORK_SITUATION_OPTION_OTHER:
            self._field_work_situation_val = container.text_input(
                "Beskriv din arbejdssituation her", ""
            )

    def _build_content(self) -> None:
        """Build the main content area."""

        if user_question := st.chat_input("Skriv dit spørgsmål eller forespørgsel her"):
            # Add the user question to the conversation
            self.current_conversation.add_user_message(text=user_question)

        self._render_conversation()

        last_message = self.current_conversation.messages[-1]
        if last_message.role == ChatMessageRole.USER:
            # Generate the query for the QA engine
            query = ParentalLeaveStatuteQuery(
                question=last_message.text,
                situational_context={
                    "arbejdsforhold": self.user_work_situation,
                },
            )

            # Run the QA engine and render the response
            self._stream_response_from_qa_engine(query=query)

    def _render_conversation(self) -> None:
        """Display the conversation."""

        # Render example questions if no conversation has been started
        if (
            # There is only one message in the conversation
            len(self.current_conversation.messages) == 1
            and
            # The message is from the assistant
            self.current_conversation.messages[0].role == ChatMessageRole.ASSISTANT
        ):
            message = self.current_conversation.messages[0]
            with st.chat_message(message.role.value):
                st.write(message.text)
                self._render_INITIAL_QUESTIONS()
        else:
            for message in self.current_conversation.messages:
                with st.chat_message(message.role.value):
                    st.write(message.text)

    def _render_INITIAL_QUESTIONS(self) -> None:
        """Render example questions to the user."""

        for question in INITIAL_QUESTIONS:
            st.button(
                f"Spørg: {question}",
                key=question,
                on_click=lambda q=question: self.current_conversation.add_user_message(
                    text=q
                ),
            )

    def _stream_response_from_qa_engine(self, query: ParentalLeaveStatuteQuery) -> None:
        """Query the QA engine and render response.

        Args:
            query (ParentalLeaveStatuteQuery): the query to send to the QA engine.
            container (DeltaGenerator): the container to render the response in.
        """
        with st.chat_message(ChatMessageRole.ASSISTANT.value):
            full_response: str = ""
            with st.spinner("Tænker..."):
                response_iter: Iterator[str] = self._qa_engine.run(query)
                placeholder = st.empty()
                for item in response_iter:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
            self.current_conversation.add_assistant_message(text=full_response)


def main() -> None:
    """Run the app."""

    # TODO: Make the following variables configurable.
    index_dir = Path("data/llama-indices/cohere-embed-v3")
    cohere_api_key: str = os.environ.get("COHERE_API_KEY", "")
    openai_api_key: str = os.environ.get("PARAGLIDE_OPENAI_API_KEY", "")

    # Initialize the QA engine and the app
    qa_engine = ParentalLeaveStatuteQAEngine(
        index_dir=index_dir,
        cohere_api_key=cohere_api_key,
        openai_api_key=openai_api_key,
    )
    app = StreamlitApp(qa_engine=qa_engine)
    app.run()


if __name__ == "__main__":
    main()
