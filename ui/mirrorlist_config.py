from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, Select

MIRROR_COUNTRIES: list[tuple[str, str]] = [
    ("France", "France"),
    ("Germany", "Germany"),
    ("Netherlands", "Netherlands"),
    ("Belgium", "Belgium"),
    ("Luxembourg", "Luxembourg"),
    ("Switzerland", "Switzerland"),
    ("Austria", "Austria"),
    ("United Kingdom", "United Kingdom"),
    ("Ireland", "Ireland"),
    ("Spain", "Spain"),
    ("Portugal", "Portugal"),
    ("Italy", "Italy"),
    ("Denmark", "Denmark"),
    ("Sweden", "Sweden"),
    ("Norway", "Norway"),
    ("Finland", "Finland"),
    ("Poland", "Poland"),
    ("Czechia", "Czechia"),
    ("Romania", "Romania"),
    ("Hungary", "Hungary"),
    ("Greece", "Greece"),
    ("Turkey", "Turkey"),
    ("Canada", "Canada"),
    ("United States", "United States"),
    ("Mexico", "Mexico"),
    ("Brazil", "Brazil"),
    ("Argentina", "Argentina"),
    ("Japan", "Japan"),
    ("South Korea", "South Korea"),
    ("Singapore", "Singapore"),
    ("India", "India"),
    ("Australia", "Australia"),
    ("New Zealand", "New Zealand"),
    ("South Africa", "South Africa"),
]


class MirrorlistConfig(Widget):
    """Floating panel to configure pacman mirrors via Reflector."""

    DEFAULT_CSS = """
    MirrorlistConfig {
        width: 60;
        height: auto;
        padding: 1 2;
        border: round $accent;
        background: $surface;
        layer: overlay;
    }

    #mirrorlist-title {
        margin-bottom: 1;
        text-style: bold;
    }

    #mirrorlist-fields {
        margin-bottom: 1;
    }

    #mirrorlist-buttons Button {
        margin-right: 1;
    }
    """

    class ApplyRequested(Message):
        """Sent when the user applies mirror configuration."""

        bubble = True

        def __init__(
            self,
            country: str,
        ) -> None:
            self.country = country
            super().__init__()

    class CloseRequested(Message):
        """Sent when the user closes the mirrorlist panel."""

        bubble = True

    def compose(
        self
    ) -> ComposeResult:
        """Build the mirrorlist configuration panel."""
        yield Label(
            "Configure mirrors",
            id="mirrorlist-title",
        )

        with Vertical(id="mirrorlist-fields"):
            yield Select(
                MIRROR_COUNTRIES,
                id="mirrorlist-country-select",
                prompt="Country",
                value="France",
            )

        with Horizontal(id="mirrorlist-buttons"):
            yield Button(
                "Apply",
                id="mirrorlist-apply",
                variant="primary",
            )
            yield Button(
                "Close",
                id="mirrorlist-close",
                variant="default",
            )

    def on_button_pressed(
        self, event: Button.Pressed
    ) -> None:
        """Handle local button actions."""
        if event.button.id == "mirrorlist-close":
            self.post_message(self.CloseRequested())
            return

        if event.button.id == "mirrorlist-apply":
            country_select = self.query_one(
                "#mirrorlist-country-select",
                Select,
            )
            selected_value = country_select.value

            if isinstance(selected_value, str):
                country = selected_value
            else:
                country = "France"

            self.post_message(self.ApplyRequested(country=country))
