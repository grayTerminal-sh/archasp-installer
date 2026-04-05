"""Configure locales, timezone and console keymap for ArchASP."""

from __future__ import annotations

from pathlib import Path
import subprocess


def _run_command(command: list[str], output_lines: list[str]) -> bool:
    """Run a command, append terminal-style output, and return success."""
    output_lines.append(f"root@archiso# {' '.join(command)}\n")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.stdout.strip():
        output_lines.append(result.stdout.strip())
        output_lines.append("")

    if result.returncode != 0:
        error = result.stderr.strip() or "Unknown error."
        output_lines.append(f"[error] {error}")
        output_lines.append("")
        output_lines.append("[abort] Localization application stopped.")
        return False

    if result.stderr.strip():
        output_lines.append(result.stderr.strip())
        output_lines.append("")

    return True


def list_system_locales() -> list[str]:
    """Return the list of available system locales.

    Prefer /usr/share/i18n/SUPPORTED when present so the user can
    pick from all supported locales, not just the ones already
    generated on the live system.
    """
    supported_path = Path("/usr/share/i18n/SUPPORTED")
    locales: list[str] = []

    if supported_path.exists():
        for line in supported_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Format typique: "fr_FR.UTF-8 UTF-8"
            locale_name = line.split()[0]
            locales.append(locale_name)
    else:
        result = subprocess.run(
            ["locale", "-a"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []

        locales.extend(
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        )

    return sorted(set(locales))


def list_timezones() -> list[str]:
    """Return the list of available timezones (Region/City)."""
    result = subprocess.run(
        ["find", "/usr/share/zoneinfo", "-type", "f"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []

    zones: list[str] = []
    prefix = "/usr/share/zoneinfo/"

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith(prefix):
            continue
        name = line.removeprefix(prefix)
        if "/" not in name:
            continue
        zones.append(name)

    return sorted(zones)


def list_console_keymaps() -> list[str]:
    """Return the list of available console keymaps."""
    result = subprocess.run(
        ["localectl", "list-keymaps"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []

    return sorted(
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    )


def _update_locale_gen(
    locale_gen_path: Path,
    locales: list[str],
) -> None:
    """Enable the requested locales in locale.gen."""
    if not locale_gen_path.exists():
        return

    wanted = set(locales)
    lines = locale_gen_path.read_text(encoding="utf-8").splitlines()
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            target = stripped.lstrip("#").strip()
            if target and any(target.startswith(loc) for loc in wanted):
                new_lines.append(target)
            else:
                new_lines.append(line)
            continue

        if any(stripped.startswith(loc) for loc in wanted):
            new_lines.append(stripped)
        else:
            new_lines.append(line)

    locale_gen_path.write_text(
        "\n".join(new_lines) + "\n",
        encoding="utf-8",
    )


def _write_locale_conf(locale_conf_path: Path, default_lang: str) -> None:
    """Write /etc/locale.conf."""
    content = f"LANG={default_lang}\n"
    locale_conf_path.write_text(content, encoding="utf-8")


def _write_vconsole_conf(vconsole_path: Path, keymap: str) -> None:
    """Write /etc/vconsole.conf."""
    content = f"KEYMAP={keymap}\n"
    vconsole_path.write_text(content, encoding="utf-8")


def apply_localization(
    mountpoint: str,
    locales: list[str],
    default_lang: str,
    timezone: str,
    keymap: str,
) -> str:
    """Configure locales, timezone and console keymap in the target system.

    This function:
    - updates /etc/locale.gen under the mountpoint,
    - writes /etc/locale.conf,
    - writes /etc/vconsole.conf,
    - runs locale-gen in an arch-chroot,
    - sets /etc/localtime and runs hwclock --systohc.
    """
    output_lines: list[str] = []

    default_lang = default_lang.strip() or "en_US.UTF-8"
    timezone = timezone.strip() or "UTC"
    keymap = keymap.strip() or "us"

    if not locales:
        return "[error] No locales selected."

    mp = Path(mountpoint)
    if not mp.exists():
        return f"[error] Mountpoint does not exist: {mountpoint}"

    etc_dir = mp / "etc"
    locale_gen_path = etc_dir / "locale.gen"
    locale_conf_path = etc_dir / "locale.conf"
    vconsole_path = etc_dir / "vconsole.conf"

    _update_locale_gen(locale_gen_path, locales)
    _write_locale_conf(locale_conf_path, default_lang)
    _write_vconsole_conf(vconsole_path, keymap)

    if not _run_command(
        [
            "arch-chroot",
            mountpoint,
            "locale-gen"
        ],
        output_lines,
    ):
        return "\n".join(output_lines)

    zoneinfo_path = f"/usr/share/zoneinfo/{timezone}"
    if not _run_command(
        [
            "arch-chroot",
            mountpoint,
            "ln",
            "-sf",
            zoneinfo_path,
            "/etc/localtime"
        ],
        output_lines,
    ):
        return "\n".join(output_lines)

    if not _run_command(
        [
            "arch-chroot",
            mountpoint,
            "hwclock",
            "--systohc"
        ],
        output_lines,
    ):
        return "\n".join(output_lines)

    output_lines.append(
        f"[ok] Localization applied with LANG={default_lang}, "
        f"TIMEZONE={timezone}, KEYMAP={keymap}."
    )

    return "\n".join(output_lines)
