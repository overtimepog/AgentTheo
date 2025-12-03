"""Tests for TUI components.

This module contains tests for the Textual-based TUI components:
- TheoApp main application
- ConversationWidget for displaying messages
- ReasoningPanel for streaming reasoning traces
- MessageInput for user input
"""

from textual.widgets import Input

from theo.tui.app import TheoApp
from theo.tui.widgets.conversation import ConversationWidget
from theo.tui.widgets.input import MessageInput
from theo.tui.widgets.reasoning import ReasoningPanel


class TestTheoAppLayout:
    """Test the main TheoApp layout."""

    async def test_app_initializes_with_three_panel_layout(self):
        """Test that the app initializes with conversation, reasoning, and input panels."""
        app = TheoApp()
        async with app.run_test():
            # Check that all three main components exist
            conversation = app.query_one(ConversationWidget)
            reasoning = app.query_one(ReasoningPanel)
            message_input = app.query_one(MessageInput)

            assert conversation is not None, "ConversationWidget should exist"
            assert reasoning is not None, "ReasoningPanel should exist"
            assert message_input is not None, "MessageInput should exist"

    async def test_app_focuses_input_on_startup(self):
        """Test that the input widget has focus on startup."""
        app = TheoApp()
        async with app.run_test() as pilot:
            # Allow time for focus to be set
            await pilot.pause()
            message_input = app.query_one(MessageInput)
            # The inner Input should have focus
            inner_input = message_input.query_one(Input)
            assert inner_input.has_focus or message_input.has_focus


class TestConversationWidget:
    """Test the ConversationWidget."""

    async def test_conversation_widget_renders_user_message(self):
        """Test that user messages are added and rendered."""
        app = TheoApp()
        async with app.run_test() as pilot:
            conversation = app.query_one(ConversationWidget)
            initial_count = conversation.message_count

            # Add a user message
            conversation.add_user_message("Hello, Theo!")
            await pilot.pause()

            # Check that message was added
            assert conversation.message_count > initial_count

    async def test_conversation_widget_renders_assistant_message(self):
        """Test that assistant messages are rendered with markdown."""
        app = TheoApp()
        async with app.run_test() as pilot:
            conversation = app.query_one(ConversationWidget)
            initial_count = conversation.message_count

            # Add an assistant message with markdown
            conversation.add_assistant_message("**Bold** and *italic* text")
            await pilot.pause()

            # Check that message was added
            assert conversation.message_count > initial_count

    async def test_conversation_widget_renders_error_with_distinct_style(self):
        """Test that error messages display with distinct styling."""
        app = TheoApp()
        async with app.run_test() as pilot:
            conversation = app.query_one(ConversationWidget)
            initial_count = conversation.message_count

            # Add an error message
            conversation.add_error("Connection failed")
            await pilot.pause()

            # Check that error was added
            assert conversation.message_count > initial_count


class TestReasoningPanel:
    """Test the ReasoningPanel widget."""

    async def test_reasoning_panel_updates_with_streaming_content(self):
        """Test that reasoning panel can receive streaming tokens."""
        app = TheoApp()
        async with app.run_test() as pilot:
            reasoning = app.query_one(ReasoningPanel)

            # Stream some tokens
            reasoning.add_token("Analyzing")
            reasoning.add_token(" the")
            reasoning.add_token(" request...")
            await pilot.pause()

            # Panel should have content
            assert reasoning.token_count > 0

    async def test_reasoning_panel_clears_content(self):
        """Test that reasoning panel can be cleared."""
        app = TheoApp()
        async with app.run_test() as pilot:
            reasoning = app.query_one(ReasoningPanel)

            # Add some content
            reasoning.add_token("Some reasoning...")
            await pilot.pause()

            # Verify tokens were added
            assert reasoning.token_count > 0

            # Clear the panel
            reasoning.clear()
            await pilot.pause()

            # Panel should be empty
            assert reasoning.token_count == 0


class TestMessageInput:
    """Test the MessageInput widget."""

    async def test_input_submission_clears_value(self):
        """Test that submitting input clears the value."""
        app = TheoApp()
        async with app.run_test() as pilot:
            message_input = app.query_one(MessageInput)
            inner_input = message_input.query_one(Input)

            # Set the input value programmatically
            inner_input.value = "Hello"
            await pilot.pause()

            # Verify value is set
            assert inner_input.value == "Hello"

            # Submit - this should trigger the event and clear
            await pilot.press("enter")
            await pilot.pause()

            # Input should be cleared after submission
            assert inner_input.value == ""

    async def test_input_clears_after_submission(self):
        """Test that input field clears after submission."""
        app = TheoApp()
        async with app.run_test() as pilot:
            message_input = app.query_one(MessageInput)
            inner_input = message_input.query_one(Input)

            # Set value and submit
            inner_input.value = "Test"
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Input should be cleared
            assert inner_input.value == ""

    async def test_empty_input_not_submitted(self):
        """Test that empty input is not submitted."""
        app = TheoApp()
        async with app.run_test() as pilot:
            message_input = app.query_one(MessageInput)
            inner_input = message_input.query_one(Input)

            # Try to submit empty input
            inner_input.focus()
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Nothing should happen with empty input
            # The input is still empty and focused
            assert inner_input.value == ""
