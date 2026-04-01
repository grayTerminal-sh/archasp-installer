"""Partitioning step widget for the ArchASP installer.

This module provides the floating panel used to choose a partitioning
scheme and generate a safe preview of the partition layout.

At this stage, the widget only simulates the partition plan. It does
not apply changes to the target disk.
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, Select, Static

from core.disks import get_disk_size_bytes
from core.partitioning import (
    render_partition_plan,
    simulate_partition_layout,
)


class PartitionDisk(Widget):
    """Floating widget used to simulate a partitioning plan."""
    selected_scheme: str | None = None
    selected_disk: str | None = None

    class SimulationRequested(Message):
        """Message sent when a partition simulation has been generated."""

        bubble = True

        def __init__(self, disk_name: str, scheme: str, preview: str) -> None:
            """Store the simulated partition preview details."""

            super().__init__()
            self.disk_name = disk_name
            self.scheme = scheme
            self.preview = preview

    class CloseRequested(Message):
        """Message sent when the user closes the partition panel."""

        bubble = True

    def compose(self) -> ComposeResult:
        """Build the partition simulation floating panel."""
        with Vertical():
            yield Label("Partition disk", id="partition-title")
            yield Label("Partitioning scheme", id="partition-section-title")

            yield Select(
                options=[
                    (
                        "UEFI simple | EFI + root",
                        "uefi-simple"
                    ),
                    (
                        "UEFI standard | EFI + swap + root",
                        "uefi-standard"
                    ),
                    (
                        "UEFI complete | EFI + swap + root + home",
                        "uefi-complete"
                    ),
                    (
                        "Manual",
                        "manual"
                    ),
                ],
                prompt="Choose a partitioning scheme",
                id="partition-scheme-select",
            )

            yield Static(
                "No scheme selected.",
                id="partition-preview"
            )

            yield Button(
                "Simulate partition plan",
                id="simulate-partition-plan",
                variant="primary"
            )

            yield Button(
                "Close",
                id="close-partition-step",
                variant="default"
            )

    def set_disk(self, disk_name: str | None) -> None:
        """Attach the currently selected installation disk to this step."""
        self.selected_disk = disk_name
        preview = self.query_one("#partition-preview", Static)

        if disk_name is None:
            preview.update("No disk selected for partitioning.")
            return

        preview.update(
            f"Selected disk for partitioning: /dev/{disk_name}\n"
            "Choose a scheme to simulate the partition layout."
        )

    def set_preview(self, content: str) -> None:
        """Update the local partition preview area."""
        preview = self.query_one("#partition-preview", Static)
        preview.update(content)

    def on_select_changed(self, event: Select.Changed) -> None:
        """React to partitioning scheme selection changes."""
        if event.select.id != "partition-scheme-select":
            return

        if event.value is Select.BLANK:
            self.selected_scheme = None
            self.set_preview("No scheme selected.")
            return

        self.selected_scheme = str(event.value)

        if self.selected_disk is None:
            self.set_preview(
                "No disk selected for partitioning.\n"
                "You must complete the disk selection step first."
            )
            return

        self.set_preview(
            f"Selected disk: /dev/{self.selected_disk}\n"
            f"Selected scheme: {self.selected_scheme}\n\n"
            "Click 'Simulate partition plan' to preview the layout."
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle local actions from the partitioning panel."""
        if event.button.id == "close-partition-step":
            self.post_message(self.CloseRequested())
            return

        if event.button.id != "simulate-partition-plan":
            return

        if self.selected_disk is None:
            self.set_preview(
                "No disk selected for partitioning.\n"
                "You must complete the disk selection step first."
            )
            return

        if self.selected_scheme is None:
            self.set_preview("You must select a partitioning scheme first.")
            return

        disk_size_bytes = get_disk_size_bytes(self.selected_disk)
        plan = simulate_partition_layout(
            disk_size_bytes,
            self.selected_scheme
        )
        preview = render_partition_plan(
            self.selected_disk,
            disk_size_bytes,
            self.selected_scheme,
            plan
        )

        self.set_preview(preview)
        self.post_message(
            self.SimulationRequested(
                self.selected_disk,
                self.selected_scheme,
                preview
            )
        )
