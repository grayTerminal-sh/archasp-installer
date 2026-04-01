"""Shared command display widget for the ArchASP installer.

This module defines the right-side panel used to display:
- command explanations in Markdown form,
- terminal-like command output,
- future step feedback during the installation workflow.
"""

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Label, Markdown, Static
from textual.widget import Widget


class CommandView(Widget):
    """Display command explanations and terminal output.

    This widget acts as the main feedback area of the application.
    Other steps update it to explain what a command does and to show
    the result of inspection or simulation actions.
    """

    def compose(self) -> ComposeResult:
        """Build the explanation and terminal output areas."""
        with Vertical(id="right-pane"):
            yield Label("Command explanation", id="explain-title")

            with VerticalScroll(id="right-pane-explanation"):
                yield Markdown(
                    "No command launched yet.",
                    id="command-explanation"
                )

            yield Label("Terminal output", id="terminal-title")

            with VerticalScroll(id="right-pane-terminal"):
                yield Static(
                    "[ready] waiting for command...",
                    id="terminal-output"
                )

    def set_explanation(self, markdown: str) -> None:
        """Update the Markdown explanation panel."""
        explanation = self.query_one("#command-explanation", Markdown)
        explanation.update(markdown)

    def set_terminal_output(self, content: str) -> None:
        """Update the terminal-like output area."""
        terminal = self.query_one("#terminal-output", Static)
        terminal.update(content)
