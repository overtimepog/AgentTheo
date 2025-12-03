"""Conversation widget for displaying chat messages.

This module provides the ConversationWidget which displays user messages
and assistant responses in a scrollable log with markdown rendering.
"""

from rich.markdown import Markdown
from rich.text import Text
from textual.widgets import RichLog


class ConversationWidget(RichLog):
    """Widget for displaying conversation messages.

    Extends RichLog to provide a scrollable conversation view with
    markdown rendering for assistant messages and distinct styling
    for different message types.

    Example:
        >>> conversation = ConversationWidget()
        >>> conversation.add_user_message("Hello!")
        >>> conversation.add_assistant_message("Hi! How can I help?")
        >>> conversation.add_error("Connection failed")
    """

    DEFAULT_CSS = """
    ConversationWidget {
        background: $surface;
        border: solid $primary;
        padding: 1;
        scrollbar-gutter: stable;
    }
    """

    def __init__(
        self,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the conversation widget.

        Args:
            id: Optional widget ID.
            classes: Optional CSS classes.
        """
        super().__init__(
            id=id,
            classes=classes,
            highlight=True,
            markup=True,
            auto_scroll=True,
            wrap=True,
        )
        self._message_count: int = 0

    @property
    def message_count(self) -> int:
        """Get the number of messages written to the widget.

        Returns:
            Count of messages added.
        """
        return self._message_count

    def add_user_message(self, text: str) -> None:
        """Add a user message to the conversation.

        User messages are displayed with a distinct prefix and styling.

        Args:
            text: The user's message text.
        """
        user_text = Text()
        user_text.append("\n")
        user_text.append("You", style="bold cyan")
        user_text.append(": ", style="bold")
        user_text.append(text)
        self.write(user_text)
        self._message_count += 1

    def add_assistant_message(self, text: str) -> None:
        """Add an assistant message to the conversation.

        Assistant messages are rendered with markdown formatting.

        Args:
            text: The assistant's message text (may contain markdown).
        """
        # Add assistant header
        header = Text()
        header.append("\n")
        header.append("Theo", style="bold green")
        header.append(": ", style="bold")
        self.write(header)

        # Render markdown content
        markdown = Markdown(text)
        self.write(markdown)
        self._message_count += 1

    def add_tool_output(self, tool_name: str, output: str) -> None:
        """Add tool execution output to the conversation.

        Tool outputs are displayed with a distinct style to differentiate
        them from regular messages.

        Args:
            tool_name: Name of the tool that was executed.
            output: The tool's output text.
        """
        tool_text = Text()
        tool_text.append("\n")
        tool_text.append(f"[{tool_name}]", style="bold yellow")
        tool_text.append("\n")
        tool_text.append(output, style="dim")
        self.write(tool_text)
        self._message_count += 1

    def add_error(self, text: str) -> None:
        """Add an error message to the conversation.

        Error messages are displayed with red/warning styling to
        make them clearly visible.

        Args:
            text: The error message text.
        """
        error_text = Text()
        error_text.append("\n")
        error_text.append("Error", style="bold red")
        error_text.append(": ", style="bold red")
        error_text.append(text, style="red")
        self.write(error_text)
        self._message_count += 1

    def add_system_message(self, text: str) -> None:
        """Add a system message to the conversation.

        System messages are displayed with dim styling for
        informational purposes.

        Args:
            text: The system message text.
        """
        system_text = Text()
        system_text.append("\n")
        system_text.append(text, style="dim italic")
        self.write(system_text)
        self._message_count += 1

    def clear(self) -> None:
        """Clear the conversation and reset message count."""
        super().clear()
        self._message_count = 0
