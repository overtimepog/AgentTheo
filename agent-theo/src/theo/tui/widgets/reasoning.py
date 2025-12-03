"""Reasoning panel widget for displaying agent thinking.

This module provides the ReasoningPanel widget which displays
streaming reasoning traces from the agent in a collapsible panel.
"""

from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Collapsible, RichLog


class ReasoningPanel(Collapsible):
    """Collapsible panel for displaying reasoning traces.

    Wraps a RichLog in a Collapsible widget to show the agent's
    reasoning process. Supports streaming tokens and auto-scrolling.

    Example:
        >>> panel = ReasoningPanel()
        >>> panel.add_token("Analyzing")
        >>> panel.add_token(" request...")
        >>> panel.clear()  # Clear for new turn
    """

    DEFAULT_CSS = """
    ReasoningPanel {
        height: 100%;
        border: solid $secondary;
    }

    ReasoningPanel > RichLog {
        background: $surface-darken-1;
        padding: 1;
        height: 100%;
    }
    """

    def __init__(
        self,
        *,
        title: str = "Reasoning",
        collapsed: bool = False,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the reasoning panel.

        Args:
            title: Title shown in the collapsible header.
            collapsed: Whether to start collapsed.
            id: Optional widget ID.
            classes: Optional CSS classes.
        """
        super().__init__(
            title=title,
            collapsed=collapsed,
            id=id,
            classes=classes,
        )
        self._current_line = Text()
        self._log: RichLog | None = None
        self._token_count: int = 0

    def compose(self) -> ComposeResult:
        """Compose the panel with a RichLog inside."""
        self._log = RichLog(
            id="reasoning-log",
            highlight=False,
            markup=True,
            auto_scroll=True,
            wrap=True,
        )
        yield self._log

    @property
    def log(self) -> RichLog:
        """Get the inner RichLog widget.

        Returns:
            The RichLog widget used for display.

        Raises:
            RuntimeError: If accessed before compose.
        """
        if self._log is None:
            raise RuntimeError("ReasoningPanel not yet composed")
        return self._log

    @property
    def token_count(self) -> int:
        """Get the number of tokens added.

        Returns:
            Count of tokens added.
        """
        return self._token_count

    @property
    def line_count(self) -> int:
        """Get the number of lines written (approximation for testing).

        Returns:
            Number of tokens added, as a proxy for content.
        """
        return self._token_count

    def add_token(self, token: str) -> None:
        """Add a streaming token to the reasoning display.

        Tokens are accumulated until a newline is encountered,
        then the line is written to the log.

        Args:
            token: The token to add (may contain newlines).
        """
        if self._log is None:
            return

        self._token_count += 1

        # Handle tokens that may contain newlines
        parts = token.split("\n")

        for i, part in enumerate(parts):
            self._current_line.append(part, style="dim cyan")

            # If this is not the last part, we have a newline
            if i < len(parts) - 1:
                self._flush_line()

    def _flush_line(self) -> None:
        """Flush the current line to the log."""
        if self._log is None:
            return

        if self._current_line.plain:
            self._log.write(self._current_line)

        self._current_line = Text()

    def add_text(self, text: str) -> None:
        """Add complete text to the reasoning display.

        Unlike add_token, this writes the text as a complete entry.

        Args:
            text: The text to add.
        """
        if self._log is None:
            return

        # Flush any pending tokens first
        self._flush_line()

        # Write the text
        styled_text = Text(text, style="dim cyan")
        self._log.write(styled_text)
        self._token_count += 1

    def clear(self) -> None:
        """Clear the reasoning panel for a new conversation turn."""
        if self._log is None:
            return

        self._log.clear()
        self._current_line = Text()
        self._token_count = 0

    def write(self, content: str | Text) -> None:
        """Write content directly to the log.

        Args:
            content: String or Text to write.
        """
        if self._log is None:
            return

        self._flush_line()

        if isinstance(content, str):
            self._log.write(Text(content, style="dim cyan"))
        else:
            self._log.write(content)
        self._token_count += 1
