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
from textual.widgets import Button, Label

import subprocess

from core.docs import (
    lsblk_explanation,
    btrfs_explanation,
    preflight_explanation,
    pacstrap_explanation,
)
from core.disks import inspect_disk
from core.system import apply_console_keymap
from core.partitioning_apply import apply_partition_layout
from core.btrfs_apply import apply_btrfs_layout
from core.mirrorlist_apply import apply_mirrorlist
# from core.locale_apply import apply_localization
from ui.choose_disk import ChooseDisk
from ui.command_view import CommandView
from ui.partition_disk import PartitionDisk
from ui.confirm_partition_apply import ConfirmPartitionApply
from ui.preflight import PreflightSetup
from ui.install_system import InstallSystem
from ui.mirrorlist_config import MirrorlistConfig
# from ui.locale import Localization


class ArchASP(App):
    """Main Textual application for the ArchASP installer.

    This class acts as the orchestrator of the interface. It does not
    implement low-level disk operations itself. Instead, it listens to
    messages emitted by child widgets and updates the shared UI state.
    """

    CSS_PATH = "style.tcss"

    selected_disk: str | None = None
    disk_step_valid: bool = False
    disk_step_open: bool = False
    partition_step_open: bool = False
    preflight_valid: bool = False
    selected_partition_scheme: str | None = None
    system_install_valid: bool = False
    install_system_step_open: bool = False
    install_system_step_valid: bool = False
    mirrorlist_step_open: bool = False
    localization_step_open: bool = False
    localization_step_valid: bool = False
    pacstrap_process: subprocess.Popen[str] | None = None

    async def _run_pacstrap_install(self) -> None:
        """Run pacstrap interactively and stream output to the install panel."""
        install_panel = self.query_one(InstallSystem)

        command = [
            "pacstrap",
            "-K",
            "/mnt",
            "base",
            "linux",
            "linux-firmware",
        ]

        self.call_from_thread(
            install_panel.post_message,
            InstallSystem.TerminalOutput(
                "root@archiso# " + " ".join(command)
            ),
        )
        self.call_from_thread(
            install_panel.post_message,
            InstallSystem.TerminalOutput(""),
        )

        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.pacstrap_process = process

        assert process.stdout is not None

        for line in process.stdout:
            self.call_from_thread(
                install_panel.post_message,
                InstallSystem.TerminalOutput(line.rstrip("\n")),
            )

        returncode = process.wait()
        self.pacstrap_process = None

        self.call_from_thread(
            install_panel.post_message,
            InstallSystem.ProcessFinished(returncode),
        )

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

        with Container(id="app-shell"):
            yield Label("ArchASP Installer", id="title")

            # Floating panels are hidden by default and opened on demand.

            yield PreflightSetup(
                id="preflight-float-panel"
            )
            yield ChooseDisk(
                id="disk-float-panel",
                classes="hidden"
            )
            yield PartitionDisk(
                id="partition-float-panel",
                classes="hidden"
            )
            yield ConfirmPartitionApply(
                id="confirm-partition-float-panel",
                classes="hidden",
            )
            yield MirrorlistConfig(
                id="mirrorlist-float-panel",
                classes="hidden",
            )
            yield InstallSystem(
                id="install-system-float-panel",
                classes="hidden",
            )
#            yield Localization(
#                id="localization-float-panel",
#                classes="hidden",
#            )

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

                    yield Button(
                        "Apply Btrfs",
                        id="apply-btrfs-layout-step",
                        variant="default",
                    )

                    yield Button(
                        "Install system",
                        id="open-install-system-step",
                        variant="default",
                    )
#                   yield Button(
#                        "Localization",
#                        id="open-localization-step",
#                        variant="default",
#                    )

                yield CommandView(id="command-view")

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

        if not self.preflight_valid:
            command_view = self.query_one(CommandView)
            panel = self.query_one("#preflight-float-panel")

            self.preflight_open = True
            panel.remove_class("hidden")
            command_view.set_terminal_output(
                "[warning] Complete the live environment setup first."
            )
            return

        if event.button.id == "open-install-system-step":
            panel = self.query_one("#install-system-float-panel")
            self.install_system_step_open = True
            panel.remove_class("hidden")
            return

#        if event.button.id == "open-localization-step":
#            panel = self.query_one("#localization-float-panel")
#
#            self.localization_step_open = True
#            panel.remove_class("hidden")
#            return

    @on(PreflightSetup.PreflightCompleted)
    def handle_preflight_completed(
        self, message: PreflightSetup.PreflightCompleted
    ) -> None:
        """Validate preflight setup and close the startup panel."""
        panel = self.query_one("#preflight-float-panel")
        command_view = self.query_one(CommandView)

        success, keymap_result = apply_console_keymap(message.keymap)

        command_view.set_explanation(
            preflight_explanation(
                message.keymap,
                message.network_mode,
            )
        )

        if not success:
            command_view.set_terminal_output(keymap_result)
            return

        self.preflight_valid = True
        self.preflight_open = False
        panel.add_class("hidden")

        if message.network_mode == "iwctl":
            command_view.set_terminal_output(
                keymap_result
                + "\n\n"
                "root@archiso# iwctl\n"
                "[iwd]# device list\n"
                "[iwd]# station DEVICE scan\n"
                "[iwd]# station DEVICE get-networks\n"
                "[iwd]# station DEVICE connect SSID"
            )
            return

        command_view.set_terminal_output(
            keymap_result
            + "\n\n"
            "[ok] Live environment preflight completed."
        )

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
        """Display the partitioning simulation in the command view."""
        command_view = self.query_one(CommandView)
        step_button = self.query_one("#open-partition-step", Button)
        confirm_panel = self.query_one(ConfirmPartitionApply)
        confirm_float = self.query_one("#confirm-partition-float-panel")

        self.partition_step_valid = True

        step_button.label = "Partition disk ✓"
        step_button.variant = "success"

        self.selected_partition_scheme = message.scheme

        command_view.set_explanation(
            btrfs_explanation()
            + "\n\n"
            "## Partition simulation\n\n"
            f"Selected disk: `/dev/{message.disk_name}`\n\n"
            f"Selected scheme: `{message.scheme}`\n\n"
            "This is only a preview. No change has been applied yet."
        )

        command_view.set_terminal_output(message.preview)

        confirm_panel.set_context(
            message.disk_name,
            message.scheme,
            message.preview,
        )
        confirm_float.remove_class("hidden")

    @on(ConfirmPartitionApply.CloseRequested)
    def handle_confirm_partition_close_requested(
        self, _message: ConfirmPartitionApply.CloseRequested
    ) -> None:
        """Close the destructive partition confirmation panel."""
        panel = self.query_one("#confirm-partition-float-panel")
        panel.add_class("hidden")

    @on(ConfirmPartitionApply.ApplyConfirmed)
    def handle_partition_apply_confirmed(
        self, message: ConfirmPartitionApply.ApplyConfirmed
    ) -> None:
        """Apply the confirmed partition layout to the selected disk."""
        panel = self.query_one("#confirm-partition-float-panel")
        command_view = self.query_one(CommandView)

        panel.add_class("hidden")

        command_view.set_terminal_output(
            f"[running] Applying partition layout"
            f"to /dev/{message.disk_name}...\n"
        )

        content = apply_partition_layout(
            message.disk_name,
            message.scheme,
        )
        command_view.set_terminal_output(content)

    @on(Button.Pressed, "#apply-btrfs-layout-step")
    def handle_apply_btrfs_layout_step(
        self
    ) -> None:
        """Apply the Btrfs subvolume layout on the selected disk."""
        command_view = self.query_one(CommandView)
        step_button = self.query_one("#apply-btrfs-layout-step", Button)

        if self.selected_disk is None:
            command_view.set_terminal_output(
                "[error] No disk selected. Complete the disk step first."
            )
            return

        if self.selected_partition_scheme is None:
            command_view.set_terminal_output(
                "[error] No partition scheme selected."
            )
            return

        command_view.set_terminal_output(
            f"[running] Applying Btrfs layout on "
            f"/dev/{self.selected_disk}...\n"
        )

        content = apply_btrfs_layout(
            self.selected_disk,
            self.selected_partition_scheme,
        )
        command_view.set_terminal_output(content)

        if (
                "[ok]" in content
                and "[abort]" not in content
                and "[error]" not in content
        ):
            step_button.label = "BTRFS apply ✓"
            step_button.variant = "success"

    @on(InstallSystem.ApplyRequested)
    def handle_install_system_apply_requested(
        self,
        _message: InstallSystem.ApplyRequested,
    ) -> None:
        """Start interactive pacstrap in the install panel."""
        command_view = self.query_one(CommandView)
        step_button = self.query_one("#open-install-system-step", Button)
        install_panel = self.query_one(InstallSystem)

        if self.selected_disk is None:
            install_panel.append_terminal_line(
                "[error] No disk selected. Complete the disk step first."
            )
            return

        if self.selected_partition_scheme is None:
            install_panel.append_terminal_line(
                "[error] No partition scheme selected."
            )
            return

        command_view.set_explanation(pacstrap_explanation())
        install_panel.clear_terminal()

        step_button.disabled = True

        self.run_worker(
            self._run_pacstrap_install,
            thread=True,
            name="pacstrap-install",
            exclusive=True,
        )

    @on(InstallSystem.MirrorlistRequested)
    def handle_mirrorlist_requested(
        self,
        _message: InstallSystem.MirrorlistRequested,
    ) -> None:
        """Open the mirrorlist configuration floating panel."""
        panel = self.query_one("#mirrorlist-float-panel")
        self.mirrorlist_step_open = True
        panel.remove_class("hidden")

    @on(InstallSystem.TerminalOutput)
    def handle_install_system_terminal_output(
        self,
        message: InstallSystem.TerminalOutput,
    ) -> None:
        """Append streamed pacstrap output to the install panel."""
        install_panel = self.query_one(InstallSystem)
        install_panel.append_terminal_line(message.text)

    @on(InstallSystem.ProcessFinished)
    def handle_install_system_process_finished(
        self,
        message: InstallSystem.ProcessFinished,
    ) -> None:
        """Handle end of interactive pacstrap process."""
        step_button = self.query_one("#open-install-system-step", Button)
        install_panel = self.query_one(InstallSystem)
        command_view = self.query_one(CommandView)

        step_button.disabled = False

        if message.returncode == 0:
            install_panel.append_terminal_line("")
            install_panel.append_terminal_line(
                "[ok] Base system installation completed."
            )
            command_view.set_terminal_output(
                "[ok] Base system installation completed."
            )
            self.install_system_step_valid = True
            step_button.label = "Install system ✓"
            step_button.variant = "success"
        else:
            install_panel.append_terminal_line("")
            install_panel.append_terminal_line(
                f"[error] pacstrap exited with status {message.returncode}."
            )
            command_view.set_terminal_output(
                f"[error] pacstrap exited with status {message.returncode}."
            )

    @on(InstallSystem.UserInputSubmitted)
    def handle_install_system_user_input_submitted(
        self,
        message: InstallSystem.UserInputSubmitted,
    ) -> None:
        """Send user input to the running pacstrap process."""
        install_panel = self.query_one(InstallSystem)

        if self.pacstrap_process is None or self.pacstrap_process.stdin is None:
            install_panel.append_terminal_line(
                "[warning] No interactive process is currently running."
            )
            return

        install_panel.append_terminal_line(f"> {message.text}")

        self.pacstrap_process.stdin.write(message.text + "\n")
        self.pacstrap_process.stdin.flush()

    @on(InstallSystem.CloseRequested)
    def handle_install_system_close_requested(
        self,
        _message: InstallSystem.CloseRequested,
    ) -> None:
        """Close the install system floating panel."""
        panel = self.query_one("#install-system-float-panel")
        self.installsystemopen = False
        panel.add_class("hidden")

    @on(MirrorlistConfig.CloseRequested)
    def handle_mirrorlist_close_requested(
        self,
        _message: MirrorlistConfig.CloseRequested,
    ) -> None:
        """Close the mirrorlist configuration panel."""
        panel = self.query_one("#mirrorlist-float-panel")
        self.mirrorlist_step_open = False
        panel.add_class("hidden")

    @on(MirrorlistConfig.ApplyRequested)
    def handle_mirrorlist_apply_requested(
        self,
        message: MirrorlistConfig.ApplyRequested,
    ) -> None:
        """Generate /etc/pacman.d/mirrorlist with Reflector."""
        command_view = self.query_one(CommandView)
        panel = self.query_one("#mirrorlist-float-panel")

        content = apply_mirrorlist(message.country)
        command_view.set_terminal_output(content)

        if "[ok]" in content and "[error]" not in content:
            self.mirrorlist_step_open = False
            panel.add_class("hidden")


#    @on(Localization.ApplyRequested)
#    def handle_localization_apply_requested(
#        self,
#        message: Localization.ApplyRequested,
#    ) -> None:
#        """Apply localization to the target system."""
#        command_view = self.query_one(CommandView)
#        step_button = self.query_one("#open-localization-step", Button)
#        panel = self.query_one("#localization-float-panel")
#
#        if self.selected_disk is None:
#            command_view.set_terminal_output(
#                "[error] No disk selected. Complete the disk step first."
#            )
#            return
#
#        if not self.partition_step_valid:
#            command_view.set_terminal_output(
#                "[error] Partition layout has not been applied yet."
#            )
#            return
#
#        content = apply_localization(
#            mountpoint="/mnt",
#            locales=message.locales,
#            default_lang=message.default_lang,
#            timezone=message.timezone,
#            keymap=message.keymap,
#        )
#        command_view.set_terminal_output(content)
#
#        if (
#            "[ok]" in content
#            and "[abort]" not in content
#            and "[error]" not in content
#        ):
#            self.localization_step_valid = True
#            self.localization_step_open = False
#            panel.add_class("hidden")
#            step_button.label = "Localization ✓"
#            step_button.variant = "success"
#
#    @on(Localization.CloseRequested)
#    def handle_localization_close_requested(
#        self,
#        message: Localization.CloseRequested,
#    ) -> None:
#        """Close the localization floating panel."""
#        panel = self.query_one("#localization-float-panel")
#
#        self.localization_step_open = False
#
#        panel.add_class("hidden")


if __name__ == "__main__":
    app = ArchASP()
    app.run()
