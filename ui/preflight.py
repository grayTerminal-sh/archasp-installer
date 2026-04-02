"""Preflight setup widget for the ArchASP installer.

This panel is displayed when the application starts. It helps the user:
- choose a console keymap,
- review Wi-Fi setup instructions if needed,
- confirm that the live environment is ready.

This step is informational and non-destructive.
"""
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, Select, Static

from core.system import list_console_keymaps


class PreflightSetup(Widget):
    """Floating widget used for early live-environment preparation."""

    selected_keymap: str | None = "us"
    selected_network_mode: str | None = None

    class PreflightCompleted(Message):
        """Message sent when the preflight step is confirmed."""

        bubble = True

        def __init__(self, keymap: str, network_mode: str) -> None:
            super().__init__()
            self.keymap = keymap
            self.network_mode = network_mode

    def compose(self) -> ComposeResult:
        """Build the preflight setup floating panel."""
        with Vertical():
            yield Label("Live environment setup", id="preflight-title")
            yield Label("Keyboard layout", id="preflight-section-title")
            yield Select(
                options=self.get_keymap_options(),
                prompt="Choose a console keymap",
                value="us",
                id="keymap-select",
            )
            yield Label("Network setup", id="preflight-network-title")

            yield Select(
                options=[
                    ("Already online", "online"),
                    ("Need Wi-Fi instructions (iwctl)", "iwctl"),
                ],
                prompt="Choose a network mode",
                id="network-mode-select",
            )

            yield Static(
                "Default keymap: `us`\n"
                "If needed, Arch uses `loadkeys <layout>`"
                "in the live console.\n\n"
                "Note: `loadkeys` affects the Linux console"
                "of the live system.\n"
                "If you are using ArchASP through SSH,"
                "your local keyboard layout\n"
                "is controlled by your SSH client and local machine.\n\n"
                "If you need Wi-Fi, choose the iwctl help mode.",
                id="preflight-help",
            )

            yield Button(
                "Apply and continue",
                id="confirm-preflight",
                variant="primary",
            )

    def set_help_text(self, content: str) -> None:
        """Update the contextual help message shown in the panel."""
        help_text = self.query_one("#preflight-help", Static)
        help_text.update(content)

    def on_select_changed(self, event: Select.Changed) -> None:
        """React to changes in keymap or network mode selection."""
        if event.select.id == "keymap-select":
            if event.value is Select.BLANK:
                self.selected_keymap = "us"
            else:
                self.selected_keymap = str(event.value)

        if event.select.id == "network-mode-select":
            if event.value is Select.BLANK:
                self.selected_network_mode = None
            else:
                self.selected_network_mode = str(event.value)

        keymap = self.selected_keymap or "us"
        network_mode = self.selected_network_mode

        if network_mode == "iwctl":
            self.set_help_text(
                f"Selected keymap: `{keymap}`\n\n"
                "To change the console layout:\n"
                f"- `loadkeys {keymap}`\n\n"
                "To connect with iwctl:\n"
                "- `iwctl`\n"
                "- `device list`\n"
                "- `station DEVICE scan`\n"
                "- `station DEVICE get-networks`\n"
                "- `station DEVICE connect SSID`"
            )
            return

        self.set_help_text(
            f"Selected keymap: `{keymap}`\n\n"
            f"To change the console layout:\n- `loadkeys {keymap}`\n\n"
            "If you already have internet access, you can continue."
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle local actions from the preflight setup panel."""
        if event.button.id != "confirm-preflight":
            return

        keymap = self.selected_keymap or "us"
        network_mode = self.selected_network_mode or "online"

        self.post_message(
            self.PreflightCompleted(
                keymap,
                network_mode,
            )
        )

    @staticmethod
    def get_keymap_options() -> list[tuple[str, str]]:
        """Build Select options from available console keymaps."""
        keymaps = list_console_keymaps()
        return [(keymap, keymap) for keymap in keymaps]
