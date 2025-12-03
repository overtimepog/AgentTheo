"""Input widget for user message entry.

This module provides the MessageInput widget which handles
user text input with history navigation and submission.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static


class MessageInput(Widget):
    """Widget for entering user messages.

    Provides a text input with:
    - Submit on Enter key
    - Input history navigation with Up/Down arrows
    - Clear after submission

    Example:
        >>> input_widget = MessageInput()
        >>> # User types and presses Enter
        >>> # MessageInput.Submitted event is posted
    """

    DEFAULT_CSS = """
    MessageInput {
        height: auto;
        width: 100%;
        padding: 0 1;
    }

    MessageInput > Horizontal {
        height: auto;
        width: 100%;
    }

    MessageInput > Horizontal > Static {
        width: auto;
        padding: 0 1 0 0;
        color: $primary;
        text-style: bold;
    }

    MessageInput > Horizontal > Input {
        width: 1fr;
        border: none;
        background: $surface;
    }

    MessageInput > Horizontal > Input:focus {
        border: none;
    }
    """

    class Submitted(Message):
        """Message sent when user submits input.

        Attributes:
            value: The submitted text.
        """

        def __init__(self, value: str) -> None:
            """Initialize the message.

            Args:
                value: The submitted text.
            """
            super().__init__()
            self.value = value

    def __init__(
        self,
        *,
        placeholder: str = "Type a message...",
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the message input widget.

        Args:
            placeholder: Placeholder text shown when empty.
            id: Optional widget ID.
            classes: Optional CSS classes.
        """
        super().__init__(id=id, classes=classes)
        self._placeholder = placeholder
        self._history: list[str] = []
        self._history_index: int = -1
        self._current_input: str = ""

    def compose(self) -> ComposeResult:
        """Compose the input widget."""
        with Horizontal():
            yield Static(">")
            yield Input(
                placeholder=self._placeholder,
                id="message-input",
            )

    def on_mount(self) -> None:
        """Focus the input on mount."""
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission.

        Args:
            event: The input submitted event.
        """
        event.stop()
        value = event.value.strip()

        if not value:
            return

        # Add to history
        if not self._history or self._history[-1] != value:
            self._history.append(value)

        # Reset history navigation
        self._history_index = -1
        self._current_input = ""

        # Clear input
        event.input.value = ""

        # Post submission message
        self.post_message(self.Submitted(value))

    def on_key(self, event) -> None:
        """Handle key events for history navigation.

        Args:
            event: The key event.
        """
        input_widget = self.query_one(Input)

        if event.key == "up":
            event.stop()
            self._navigate_history(-1, input_widget)
        elif event.key == "down":
            event.stop()
            self._navigate_history(1, input_widget)

    def _navigate_history(self, direction: int, input_widget: Input) -> None:
        """Navigate through input history.

        Args:
            direction: -1 for older, 1 for newer.
            input_widget: The input widget to update.
        """
        if not self._history:
            return

        # Save current input if starting navigation
        if self._history_index == -1 and direction == -1:
            self._current_input = input_widget.value

        # Calculate new index
        new_index = self._history_index + direction

        if direction == -1:
            # Going back in history
            if new_index < -len(self._history):
                return  # At oldest
            self._history_index = new_index
            input_widget.value = self._history[self._history_index]
        else:
            # Going forward in history
            if new_index > -1:
                # Return to current input
                self._history_index = -1
                input_widget.value = self._current_input
            else:
                self._history_index = new_index
                input_widget.value = self._history[self._history_index]

        # Move cursor to end
        input_widget.cursor_position = len(input_widget.value)

    def focus_input(self) -> None:
        """Focus the text input."""
        self.query_one(Input).focus()

    def clear(self) -> None:
        """Clear the input field."""
        self.query_one(Input).value = ""
