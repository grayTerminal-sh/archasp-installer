"""Apply pacman mirrorlist configuration with Reflector."""

from __future__ import annotations

import subprocess


def apply_mirrorlist(country: str) -> str:
    """Generate /etc/pacman.d/mirrorlist with Reflector."""
    command = [
        "reflector",
        "--country",
        country,
        "--latest",
        "20",
        "--protocol",
        "https",
        "--sort",
        "rate",
        "--save",
        "/etc/pacman.d/mirrorlist",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    output_lines: list[str] = [
        "root@archiso# " + " ".join(command),
        "",
    ]

    if result.stdout.strip():
        output_lines.append(result.stdout.strip())
        output_lines.append("")

    if result.stderr.strip():
        output_lines.append(result.stderr.strip())
        output_lines.append("")

    if result.returncode != 0:
        output_lines.append(
            "[error] Reflector failed. Check network and installed packages."
        )
    else:
        output_lines.append(
            "[ok] /etc/pacman.d/mirrorlist updated."
        )

    return "\n".join(output_lines)
