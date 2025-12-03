"""Main TUI application for Theo Agent.

This module contains the entry point and main Textual application class
that orchestrates the container lifecycle, agent, and user interface.
"""

from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Footer, Header

from theo.tui.widgets.conversation import ConversationWidget
from theo.tui.widgets.input import MessageInput
from theo.tui.widgets.reasoning import ReasoningPanel

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

    from theo.container.manager import ContainerManager


class TheoApp(App):
    """Theo Agent TUI Application.

    A Claude Code-style terminal interface for the Theo security
    research assistant. Features a three-panel layout with:
    - Conversation area for user/assistant messages
    - Collapsible reasoning panel for agent thinking
    - Input area for user messages

    The app manages the container lifecycle and agent integration,
    spawning a fresh Kali container on startup and destroying it on exit.
    """

    TITLE = "Theo Agent"
    SUB_TITLE = "Security Research Assistant"

    CSS = """
    TheoApp {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto auto;
    }

    #main-content {
        width: 100%;
        height: 100%;
    }

    #conversation-container {
        width: 2fr;
        height: 100%;
        min-width: 40;
    }

    #reasoning-container {
        width: 1fr;
        height: 100%;
        min-width: 30;
        max-width: 60;
    }

    #input-container {
        height: auto;
        width: 100%;
        padding: 1;
        background: $surface;
        border-top: solid $primary-darken-2;
    }

    ConversationWidget {
        height: 100%;
    }

    ReasoningPanel {
        height: 100%;
    }

    MessageInput {
        height: auto;
        width: 100%;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+r", "toggle_reasoning", "Toggle Reasoning"),
        ("ctrl+l", "clear_conversation", "Clear"),
    ]

    def __init__(self) -> None:
        """Initialize the Theo application."""
        super().__init__()
        self._container_manager: ContainerManager | None = None
        self._agent: CompiledStateGraph | None = None
        self._conversation_history: list = []
        self._is_processing: bool = False

    @property
    def container_manager(self) -> "ContainerManager | None":
        """Get the container manager instance."""
        return self._container_manager

    @property
    def agent(self) -> "CompiledStateGraph | None":
        """Get the agent instance."""
        return self._agent

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header(show_clock=True)

        with Horizontal(id="main-content"):
            with Container(id="conversation-container"):
                yield ConversationWidget(id="conversation")

            with Container(id="reasoning-container"):
                yield ReasoningPanel(
                    id="reasoning",
                    title="Reasoning",
                    collapsed=False,
                )

        with Container(id="input-container"):
            yield MessageInput(id="message-input")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize container and agent on startup."""
        conversation = self.query_one(ConversationWidget)
        conversation.add_system_message("Starting Theo Agent...")
        conversation.add_system_message("Initializing Kali Linux container...")

        # Start container initialization in background
        self.initialize_agent()

    @work(exclusive=True)
    async def initialize_agent(self) -> None:
        """Initialize the container and agent in a background worker."""
        conversation = self.query_one(ConversationWidget)

        try:
            # Import here to avoid circular imports and allow testing without Docker
            from theo.config import Settings
            from theo.container.manager import ContainerManager

            # Load configuration
            try:
                config = Settings()
            except Exception as e:
                conversation.add_error(f"Configuration error: {e}")
                conversation.add_system_message(
                    "Please set OPENROUTER_API_KEY environment variable."
                )
                return

            # Start container
            self._container_manager = ContainerManager()
            await self._container_manager.start()
            conversation.add_system_message("Container started successfully.")

            # Create agent
            from theo.agent.graph import create_agent

            self._agent = create_agent(self._container_manager, config)
            conversation.add_system_message("Agent initialized. Ready to assist!")
            conversation.add_system_message("")
            conversation.add_system_message(
                "Type your security research questions or commands below."
            )

        except Exception as e:
            error_msg = str(e)
            if "Docker" in error_msg or "docker" in error_msg:
                conversation.add_error("Docker is not available.")
                conversation.add_system_message(
                    "Please ensure Docker Desktop is running and try again."
                )
            else:
                conversation.add_error(f"Initialization failed: {error_msg}")

    async def on_unmount(self) -> None:
        """Cleanup container on exit."""
        if self._container_manager is not None:
            try:
                await self._container_manager.stop()
            except Exception:
                pass  # Best effort cleanup

    def on_message_input_submitted(self, event: MessageInput.Submitted) -> None:
        """Handle user input submission.

        Args:
            event: The submission event with user's message.
        """
        if self._is_processing:
            return

        # Process the message
        self.run_worker(self.handle_user_input(event.value))

    async def handle_user_input(self, message: str) -> None:
        """Process user input through the agent.

        Args:
            message: The user's message text.
        """
        if self._agent is None:
            conversation = self.query_one(ConversationWidget)
            conversation.add_error("Agent not initialized. Please wait for startup.")
            return

        self._is_processing = True
        conversation = self.query_one(ConversationWidget)
        reasoning = self.query_one(ReasoningPanel)

        # Clear reasoning for new turn
        reasoning.clear()

        # Add user message to conversation
        conversation.add_user_message(message)

        # Add to conversation history
        self._conversation_history.append(HumanMessage(content=message))

        try:
            # Stream agent response
            current_response = ""
            current_tool_calls = []

            async for chunk, metadata in self._agent.astream(
                {"messages": self._conversation_history},
                stream_mode="messages",
            ):
                # Handle different message types
                if isinstance(chunk, AIMessageChunk):
                    # Stream content to reasoning panel (thinking)
                    if chunk.content:
                        reasoning.add_token(str(chunk.content))
                        current_response += str(chunk.content)

                    # Track tool calls
                    if chunk.tool_calls:
                        current_tool_calls.extend(chunk.tool_calls)

                elif isinstance(chunk, AIMessage):
                    # Final AI message
                    if chunk.content and not current_response:
                        current_response = str(chunk.content)

                elif isinstance(chunk, ToolMessage):
                    # Tool execution result
                    tool_name = chunk.name or "Tool"
                    conversation.add_tool_output(tool_name, str(chunk.content))

            # Add final assistant response to conversation
            if current_response:
                conversation.add_assistant_message(current_response)
                self._conversation_history.append(AIMessage(content=current_response))

        except Exception as e:
            error_msg = str(e)
            if "API" in error_msg or "api" in error_msg:
                conversation.add_error(f"API error: {error_msg}")
            else:
                conversation.add_error(f"Error: {error_msg}")

        finally:
            self._is_processing = False
            # Suppress warning about unused variable
            _ = current_tool_calls

    def action_toggle_reasoning(self) -> None:
        """Toggle the reasoning panel visibility."""
        reasoning = self.query_one(ReasoningPanel)
        reasoning.collapsed = not reasoning.collapsed

    def action_clear_conversation(self) -> None:
        """Clear the conversation history."""
        conversation = self.query_one(ConversationWidget)
        reasoning = self.query_one(ReasoningPanel)

        conversation.clear()
        reasoning.clear()
        self._conversation_history.clear()

        conversation.add_system_message("Conversation cleared.")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def main() -> None:
    """Entry point for the Theo Agent TUI application."""
    app = TheoApp()
    app.run()


if __name__ == "__main__":
    main()
