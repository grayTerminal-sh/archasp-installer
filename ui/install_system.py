from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Log


class InstallSystem(Widget):
    """Floating panel to install the base system."""

    DEFAULT_CSS = """
    InstallSystem {
        width: 90;
        height: auto;
        max-height: 90%;
        padding: 1 2;
        border: wide $accent;
        background: $surface;
        layer: overlay;
    }

    #install-system-title {
        margin-bottom: 1;
        text-style: bold;
    }

    #install-system-help {
        margin-bottom: 1;
        color: $text-muted;
    }

    #install-system-terminal {
        height: 8;
        margin-bottom: 1;
        border: wide $panel;
    }

    #install-system-input-row {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
    }

    #install-system-user-input {
        width: 50%;
        margin: 0 1 0 0;
    }

    #install-system-send-input {
        width: 12;
        content-align: center middle;
        text-align: center;
    }

    #install-system-buttons Button {
        margin-right: 1;
    }
    """

    class ApplyRequested(Message):
        """Sent when the user starts the install."""
        bubble = True

    class CloseRequested(Message):
        """Sent when the user closes the panel."""
        bubble = True

    class MirrorlistRequested(Message):
        """Sent when the user wants to configure mirrors."""
        bubble = True

    class UserInputSubmitted(Message):
        """Sent when the user submits terminal input."""

        bubble = True

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    class TerminalOutput(Message):
        """Append one line to the embedded terminal."""
        bubble = True

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    class ProcessFinished(Message):
        """Notify that the interactive pacstrap process ended."""
        bubble = True

        def __init__(self, returncode: int) -> None:
            self.returncode = returncode
            super().__init__()

    def compose(self) -> ComposeResult:
        """Build the install system panel."""
        yield Label(
            "Install base system",
            id="install-system-title",
        )
        yield Label(
            "This panel will show pacstrap output. "
            "You can send input here if a prompt appears.",
            id="install-system-help",
        )

        yield Log(id="install-system-terminal")

        with Horizontal(id="install-system-input-row"):
            yield Input(
                placeholder="Type a response and press Send",
                id="install-system-user-input",
            )
            yield Button(
                "Send",
                id="install-system-send-input",
                variant="default",
            )

        with Vertical(id="install-system-buttons"):
            yield Button(
                "Configure mirrors",
                id="open-mirrorlist-step",
                variant="default",
            )
            yield Button(
                "Install system",
                id="confirm-install-system",
                variant="primary",
            )
            yield Button(
                "Close",
                id="close-install-system",
                variant="default",
            )

    def append_terminal_line(self, content: str) -> None:
        """Append one line to the embedded terminal log."""
        terminal = self.query_one("#install-system-terminal", Log)
        terminal.write_line(content)

    def clear_terminal(self) -> None:
        """Clear the embedded terminal log."""
        terminal = self.query_one("#install-system-terminal", Log)
        terminal.clear()

    def _submit_user_input(self) -> None:
        """Submit the current input value."""
        input_widget = self.query_one("#install-system-user-input", Input)
        text = input_widget.value.strip()

        if not text:
            return

        self.post_message(self.UserInputSubmitted(text))
        input_widget.value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle local button actions."""
        if event.button.id == "open-mirrorlist-step":
            self.post_message(self.MirrorlistRequested())
            return

        if event.button.id == "confirm-install-system":
            self.post_message(self.ApplyRequested())
            return

        if event.button.id == "close-install-system":
            self.post_message(self.CloseRequested())
            return

        if event.button.id == "install-system-send-input":
            self._submit_user_input()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Submit input when the user presses Enter."""
        if event.input.id == "install-system-user-input":
            self._submit_user_input()
