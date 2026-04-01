"""Main application entry point for the ArchASP installer UI.

This module defines the top-level Textual application. The app is
responsible for assembling the main widgets, opening and closing
floating panels, and coordinating data exchanged between steps.

The goal is to keep business logic in core modules and UI-specific
behavior in dedicated widgets.
"""

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Label

from core.docs import lsblk_explanation
from core.disks import inspect_disk
from ui.choose_disk import ChooseDisk
from ui.command_view import CommandView
from ui.partition_disk import PartitionDisk


class ArchASP(App):
    """Main Textual application for the ArchASP installer.

    This class acts as the orchestrator of the interface. It does not
    implement low-level disk operations itself. Instead, it listens to
    messages emitted by child widgets and updates the shared UI state.
    """

    CSS_PATH = "style.tcss"

    # Shared state between installation steps.
    selected_disk: str | None = None
    disk_step_valid: bool = False
    disk_step_open: bool = False
    partition_step_open: bool = False

    def compose(
        self
    ) -> ComposeResult:
        """Build the global application layout.

        The layout is made of:
        - a header and footer,
        - floating step panels,
        - a left-side action panel,
        - a right-side command and output panel.
        """
        yield Header()

        with Container(id="app-shell"):
            yield Label("ArchASP Installer", id="title")

            # Floating panels are hidden by default and opened on demand.

            yield ChooseDisk(id="disk-float-panel", classes="hidden")
            yield PartitionDisk(id="partition-float-panel", classes="hidden")

            with Horizontal():
                with Vertical(id="left-panel"):
                    yield Button(
                        "Find disk",
                        id="open-disk-step",
                        variant="default"
                    )

                    yield Button(
                        "Partition disk",
                        id="open-partition-step",
                        variant="default"
                    )

                yield CommandView(id="command-view")

        yield Footer()

    def on_button_pressed(
        self, event: Button.Pressed
    ) -> None:
        """Handle top-level action buttons from the left panel."""
        if event.button.id == "open-disk-step":
            panel = self.query_one("#disk-float-panel")
            self.disk_step_open = True
            panel.remove_class("hidden")
            return

        if event.button.id == "open-partition-step":
            panel = self.query_one("#partition-float-panel")
            partition_view = self.query_one(PartitionDisk)

            self.partition_step_open = True
            panel.remove_class("hidden")
            partition_view.set_disk(self.selected_disk)
            return

    @on(ChooseDisk.DiskHighlighted)
    def handle_disk_highlighted(
        self, message: ChooseDisk.DiskHighlighted
    ) -> None:
        """Reflect the currently highlighted disk in the terminal view."""
        command_view = self.query_one(CommandView)

        if message.disk_name is None:
            command_view.set_terminal_output(
                "[ready] waiting for a command..."
            )
            return

        command_view.set_terminal_output(
            f"[selected] /dev/{message.disk_name}"
        )

    @on(ChooseDisk.CloseRequested)
    def handle_choose_disk_close_requested(
        self, _message: ChooseDisk.CloseRequested
    ) -> None:
        """Close the disk selection floating panel."""
        panel = self.query_one("#disk-float-panel")
        self.disk_step_open = False
        panel.add_class("hidden")

    @on(PartitionDisk.CloseRequested)
    def handle_partition_close_requested(
        self, _message: PartitionDisk.CloseRequested
    ) -> None:
        """Close the partitioning floating panel."""
        panel = self.query_one("#partition-float-panel")
        self.partition_step_open = False
        panel.add_class("hidden")

    @on(ChooseDisk.DiskSelected)
    def handle_disk_selected(
        self, message: ChooseDisk.DiskSelected
    ) -> None:
        """Validate disk selection and display inspection output.

        Once a disk is confirmed, the app:
        - stores it as the current installation target,
        - marks the disk step as completed,
        - closes the selection panel,
        - updates the command explanation,
        - runs lsblk inspection,
        - displays the result in the command view.
        """
        self.selected_disk = message.disk_name

        panel = self.query_one("#disk-float-panel")
        command_view = self.query_one(CommandView)
        step_button = self.query_one("#open-disk-step", Button)

        self.disk_step_valid = True
        self.disk_step_open = False

        panel.add_class("hidden")

        step_button.label = "Find disk ✓"
        step_button.variant = "success"

        command_view.set_explanation(
            lsblk_explanation(self.selected_disk)
        )

        command_view.set_terminal_output(
            f"root@archiso# lsblk /dev/{self.selected_disk} "
            "-o NAME,SIZE,TYPE,MOUNTPOINT\n\n"
            "Running command..."
        )

        content = inspect_disk(self.selected_disk)
        command_view.set_terminal_output(content)

    @on(PartitionDisk.SimulationRequested)
    def handle_partition_simulation_requested(
        self, message: PartitionDisk.SimulationRequested
    ) -> None:
        """Display the partitioning simulation in the command view.

        This step only shows a preview. No partition is created yet.
        """
        command_view = self.query_one(CommandView)

        command_view.set_explanation(
            "## Partition simulation\n\n"
            f"Selected disk: `/dev/{message.disk_name}`\n\n"
            f"Selected scheme: `{message.scheme}`\n\n"
            "This is only a preview. No change has been applied yet."
        )

        command_view.set_terminal_output(message.preview)


if __name__ == "__main__":
    app = ArchASP()
    app.run()
