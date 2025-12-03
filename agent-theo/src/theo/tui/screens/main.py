"""Main screen layout for Theo Agent TUI.

This module provides the MainScreen which organizes the three-panel
layout: conversation area, reasoning panel, and input widget.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header

from theo.tui.widgets.conversation import ConversationWidget
from theo.tui.widgets.input import MessageInput
from theo.tui.widgets.reasoning import ReasoningPanel


class MainScreen(Screen):
    """Main screen with three-panel layout.

    Layout:
    +---------------------------+-------------+
    |                           |  Reasoning  |
    |    Conversation Area      |   Panel     |
    |    (RichLog + Markdown)   | (Collapsible|
    |                           |  RichLog)   |
    +---------------------------+-------------+
    |        Input Area (Input widget)        |
    +-----------------------------------------+

    The conversation area takes the majority of space while the
    reasoning panel is collapsible on the right side.
    """

    DEFAULT_CSS = """
    MainScreen {
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
    ]

    def compose(self) -> ComposeResult:
        """Compose the main screen layout."""
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

    def action_toggle_reasoning(self) -> None:
        """Toggle the reasoning panel visibility."""
        reasoning = self.query_one(ReasoningPanel)
        reasoning.collapsed = not reasoning.collapsed

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
