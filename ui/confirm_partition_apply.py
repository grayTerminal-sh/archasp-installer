"""Danger confirmation widget for applying a partition layout."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Static


class ConfirmPartitionApply(Widget):
    """Floating widget used to confirm destructive partition changes."""

    disk_name: str | None = None
    scheme: str | None = None
    summary: str = ""

    class ApplyConfirmed(Message):
        """Message sent when destructive partition application is confirmed."""

        bubble = True

        def __init__(self, disk_name: str, scheme: str) -> None:
            super().__init__()
            self.disk_name = disk_name
            self.scheme = scheme

    class CloseRequested(Message):
        """Message sent when the confirmation panel should close."""

        bubble = True

    def compose(self) -> ComposeResult:
        """Build the destructive confirmation panel."""
        with Vertical():
            yield Label("Dangerous action", id="confirm-partition-title")

            yield Static(
                "You are about to erase and repartition a disk.",
                id="confirm-partition-warning",
            )

            yield Static(
                "No disk selected.",
                id="confirm-partition-summary",
            )

            yield Label(
                "Type the disk name to confirm (example: sda)",
                id="confirm-partition-label",
            )

            yield Input(
                placeholder="Type disk name to unlock confirmation",
                id="confirm-disk-name-input",
            )

            yield Button(
                "Erase disk and apply partition layout",
                id="confirm-partition-apply",
                variant="error",
                disabled=True,
            )

            yield Button(
                "Cancel and go back",
                id="cancel-partition-apply",
                variant="default",
            )

    def set_context(self, disk_name: str, scheme: str, summary: str) -> None:
        """Fill the panel with the destructive action summary."""
        self.disk_name = disk_name
        self.scheme = scheme
        self.summary = summary

        summary_widget = self.query_one("#confirm-partition-summary", Static)
        summary_widget.update(
            f"Target disk: /dev/{disk_name}\n"
            f"Selected scheme: {scheme}\n\n"
            f"{summary}\n\n"
            "Warning:\n"
            "- All existing partition data on this disk will be destroyed\n"
            "- This action cannot be undone\n"
            "- Make sure you selected the correct disk"
        )

        input_widget = self.query_one("#confirm-disk-name-input", Input)
        input_widget.value = ""

        confirm_button = self.query_one("#confirm-partition-apply", Button)
        confirm_button.disabled = True

    def on_input_changed(self, event: Input.Changed) -> None:
        """Enable the destructive button only when the disk name matches."""
        if event.input.id != "confirm-disk-name-input":
            return

        confirm_button = self.query_one("#confirm-partition-apply", Button)

        if self.disk_name is None:
            confirm_button.disabled = True
            return

        confirm_button.disabled = event.value.strip() != self.disk_name

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle local destructive confirmation actions."""
        if event.button.id == "cancel-partition-apply":
            self.post_message(self.CloseRequested())
            return

        if event.button.id != "confirm-partition-apply":
            return

        if self.disk_name is None or self.scheme is None:
            return

        self.post_message(
            self.ApplyConfirmed(
                self.disk_name,
                self.scheme,
            )
        )
