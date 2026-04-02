"""Helpers for live system setup commands."""

import subprocess


def list_console_keymaps() -> list[str]:
    """Return available console keymaps from the live system."""
    result = subprocess.run(
        ["localectl", "list-keymaps"],
        capture_output=True,
        text=True,
        check=True,
    )

    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def apply_console_keymap(keymap: str) -> tuple[bool, str]:
    """Apply a console keymap for the current live session."""
    result = subprocess.run(
        ["loadkeys", keymap],
        capture_output=True,
        text=True,
    )

    command = f"root@archiso# loadkeys {keymap}\n\n"

    if result.returncode == 0:
        return True, command + f"[ok] Console keymap set to '{keymap}'."

    error = result.stderr.strip() or "Unknown error."
    return (
        False,
        command + f"[error] Failed to apply keymap '{keymap}'.\n\n{error}",
    )
