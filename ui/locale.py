from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, Select

from core.locale_apply import (
    list_console_keymaps,
    list_system_locales,
    list_timezones,
)


class Localization(Widget):
    """Floating panel used to configure locales,
    timezone and console keymap."""

    DEFAULT_CSS = """
    Localization {
        layout: vertical;
        width: 60%;
        height: auto;
        border: round $accent;
        padding: 1 2;
        background: $panel;
    }

    #localization-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #localization-section-title {
        color: $text-muted;
        margin-top: 1;
        margin-bottom: 1;
    }

    #localization-selects Select {
        width: 100%;
        margin-bottom: 1;
    }

    #localization-buttons {
        margin-top: 1;
        width: 100%;
        align-horizontal: right;
    }
    """

    class ApplyRequested(Message):
        """Sent when the user requests localization to be applied."""

        bubble = True

        def __init__(
            self,
            locales: list[str],
            default_lang: str,
            timezone: str,
            keymap: str,
        ) -> None:
            super().__init__()
            self.locales = locales
            self.default_lang = default_lang
            self.timezone = timezone
            self.keymap = keymap

    class CloseRequested(Message):
        """Sent when the user closes the localization panel."""

        bubble = True

    def compose(
        self
    ) -> ComposeResult:
        """Build the localization floating panel."""
        yield Label("Localization", id="localization-title")

        yield Label("Locales", classes="localization-section-title")
        yield Select[tuple[str, str]](
            [],
            id="default-locale-select",
            prompt="Choose default locale (LANG)",
        )
        yield Select[tuple[str, str]](
            [],
            id="extra-locale-select",
            prompt="Optional extra locale to generate",
            allow_blank=True,
        )

        yield Label("Timezone", classes="localization-section-title")
        yield Select[tuple[str, str]](
            [],
            id="timezone-select",
            prompt="Choose timezone (Region/City)",
        )

        yield Label("Console keymap", classes="localization-section-title")
        yield Select[tuple[str, str]](
            [],
            id="keymap-select",
            prompt="Choose TTY keymap",
        )

        with Vertical(id="localization-buttons"):
            yield Button(
                "Apply localization",
                id="apply-localization",
                variant="primary",
            )
            yield Button(
                "Close",
                id="close-localization",
                variant="default",
            )

    def on_mount(
        self
    ) -> None:
        """Populate selects from system data."""
        locales = list_system_locales()
        timezones = list_timezones()
        keymaps = list_console_keymaps()

        default_locale_select = self.query_one(
            "#default-locale-select",
            Select
        )
        extra_locale_select = self.query_one(
            "#extra-locale-select",
            Select
        )
        timezone_select = self.query_one(
            "#timezone-select",
            Select
        )
        keymap_select = self.query_one(
            "#keymap-select",
            Select
        )

        if locales:
            default_locale_select.set_options(
                [(loc, loc) for loc in locales]
            )
            extra_locale_select.set_options(
                [("", "")] + [(loc, loc) for loc in locales]
            )
            # Essaye de pré-sélectionner fr_FR.UTF-8 ou en_US.UTF-8 si dispo
            preferred = next(
                (
                    loc
                    for loc in (
                        "fr_FR.utf8",
                        "fr_FR.UTF-8",
                        "en_US.utf8",
                        "en_US.UTF-8"
                    )
                    if loc in locales
                ),
                None,
            )
            if preferred:
                default_locale_select.value = preferred

        if timezones:
            timezone_select.set_options(
                [(tz, tz) for tz in timezones]
            )
            if "Europe/Paris" in timezones:
                timezone_select.value = "Europe/Paris"

        if keymaps:
            keymap_select.set_options(
                [(km, km) for km in keymaps]
            )
            if "fr-latin1" in keymaps:
                keymap_select.value = "fr-latin1"

    def on_button_pressed(
        self,
        event: Button.Pressed
    ) -> None:
        """Handle local actions from the localization panel."""
        if event.button.id == "close-localization":
            self.post_message(self.CloseRequested())
            return

        if event.button.id != "apply-localization":
            return

        default_locale_select = self.query_one(
            "#default-locale-select", Select
        )
        extra_locale_select = self.query_one(
            "#extra-locale-select",
            Select
        )
        timezone_select = self.query_one(
            "#timezone-select",
            Select
        )
        keymap_select = self.query_one(
            "#keymap-select",
            Select
        )

        default_lang = default_locale_select.value
        extra_locale = extra_locale_select.value
        timezone = timezone_select.value
        keymap = keymap_select.value

        if default_lang is None or timezone is None or keymap is None:
            return

        locales: list[str] = [str(default_lang)]
        if extra_locale not in (
            None,
            "",
            default_lang
        ):
            locales.append(str(extra_locale))

        self.post_message(
            self.ApplyRequested(
                locales=locales,
                default_lang=str(default_lang),
                timezone=str(timezone),
                keymap=str(keymap),
            )
        )
