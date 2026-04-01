"""Disk selection panel for the ArchASP installer UI."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, Select, Static

from core.disks import detect_disks


class ChooseDisk(Widget):
    """Floating widget used to select a target installation disk."""

    selected_disk: str | None = None

    class DiskSelected(Message):
        """Message sent when the user confirms the selected disk."""

        bubble = True

        def __init__(self, disk_name: str) -> None:
            super().__init__()
            self.disk_name = disk_name

    class CloseRequested(Message):
        """Message sent when the user requests to close the panel."""

        bubble = True

    class DiskHighlighted(Message):
        """Message sent when the highlighted disk changes."""

        bubble = True

        def __init__(self, disk_name: str | None) -> None:
            super().__init__()
            self.disk_name = disk_name

    @staticmethod
    def get_disk_options(
    ) -> list[tuple[str, str]]:
        """Build Select options from detected block devices."""
        disks = detect_disks()
        options: list[tuple[str, str]] = []

        for disk in disks:
            disk_label = (
                f"{disk['name']} | {disk['size']} | "
                f"{disk['model']} | {disk['tran']}"
            )
            options.append((disk_label, disk["name"]))

        return options

    def compose(
        self
    ) -> ComposeResult:
        """Build the floating panel used to select an installation disk."""
        options = self.get_disk_options()

        with Vertical():
            yield Label("Disk step details", id="float-title")
            yield Label("Available disks", id="section-title")

            if not options:
                yield Static("No disk detected.", id="disk-label")

                yield Button(
                    "Close",
                    id="close-disk-step",
                    variant="default"
                )
                return

            yield Select(
                options=options,
                prompt="Choose a disk",
                id="disk-select"
            )

            yield Static("No disk selected.", id="disk-info")

            yield Button(
                "Select",
                id="run-select-disk",
                variant="primary"
            )

            yield Static(
                "Select disk for installation",
                id="disk-help"
            )

            yield Button(
                "Close",
                id="close-disk-step",
                variant="default"
            )

    def set_disk_info(self, content: str) -> None:
        """Update the label that describes the currently selected disk."""
        disk_info = self.query_one("#disk-info", Static)
        disk_info.update(content)

    def set_help_text(self, content: str) -> None:
        """Update the contextual help message shown in the panel."""
        help_text = self.query_one("#disk-help", Static)
        help_text.update(content)

    def on_select_changed(self, event: Select.Changed) -> None:
        """React to changes in the disk selection widget."""
        if event.select.id != "disk-select":
            return

        if event.value is Select.BLANK:
            self.selected_disk = None
            self.set_disk_info("No disk selected.")
            self.set_help_text("Select disk for installation")
            self.post_message(self.DiskHighlighted(None))
            return

        self.selected_disk = str(event.value)
        self.set_disk_info(f"Selected disk: /dev/{self.selected_disk}")
        self.set_help_text(
            f"Selected installation target: /dev/{self.selected_disk}"
        )
        self.post_message(self.DiskHighlighted(self.selected_disk))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle local button actions for the disk selection step."""
        if event.button.id == "close-disk-step":
            self.post_message(self.CloseRequested())
            return

        if event.button.id != "run-select-disk":
            return

        if self.selected_disk is None:
            self.set_disk_info("You must select a disk first.")
            self.set_help_text("Select a disk before continuing.")
            return

        self.post_message(self.DiskSelected(self.selected_disk))
