"""Install the base Arch system for ArchASP."""

from __future__ import annotations

from pathlib import Path
import subprocess

DEBUG_LOG = Path("/tmp/archasp-pacstrap.log")


def _log_debug(message: str) -> None:
    with DEBUG_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(message.rstrip() + "\n")


def _run_command(command: list[str], output_lines: list[str]) -> bool:
    output_lines.append(f"root@archiso# {' '.join(command)}\n")
    _log_debug(f"$ {' '.join(command)}")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    _log_debug(f"returncode={result.returncode}")

    if result.stdout:
        _log_debug("STDOUT:")
        _log_debug(result.stdout)

    if result.stderr:
        _log_debug("STDERR:")
        _log_debug(result.stderr)

    if result.stdout.strip():
        output_lines.append(result.stdout.strip())
        output_lines.append("")

    if result.returncode != 0:
        error = result.stderr.strip() or "Unknown error."
        output_lines.append(f"[error] {error}")
        output_lines.append("")
        output_lines.append("[abort] System installation stopped.")
        return False

    if result.stderr.strip():
        output_lines.append(result.stderr.strip())
        output_lines.append("")

    return True


def apply_pacstrap(
    mountpoint: str = "/mnt",
    extra_packages: list[str] | None = None,
) -> str:
    """Install the base system into the given mountpoint and generate fstab."""
    DEBUG_LOG.write_text("", encoding="utf-8")
    _log_debug("=== apply_pacstrap start ===")

    output_lines: list[str] = []

    mp = Path(mountpoint)
    if not mp.exists():
        return f"[error] Mountpoint does not exist: {mountpoint}"

    if not (mp / "boot" / "efi").exists():
        output_lines.append(
            "[warning] /mnt/boot/efi does not exist yet. "
            "Make sure the Btrfs and EFI mounts are ready before pacstrap."
        )
        output_lines.append("")

    output_lines.append(
        "[info] Starting base system installation. "
        "This may take several minutes depending on mirrors."
    )
    output_lines.append("")

    base_command: list[str] = [
        "pacstrap",
        mountpoint,
        "base",
        "linux",
        "linux-firmware",
        "iptables-nft",
    ]

    if extra_packages:
        base_command.extend(extra_packages)

    if not _run_command(base_command, output_lines):
        return "\n".join(output_lines)

    etc_dir = mp / "etc"
    etc_dir.mkdir(parents=True, exist_ok=True)
    fstab_path = etc_dir / "fstab"

    output_lines.append(
        "[info] Generating fstab from mounted filesystems."
    )
    output_lines.append("")
    output_lines.append(
        "root@archiso# genfstab -U /mnt > /mnt/etc/fstab\n"
    )

    result = subprocess.run(
        ["genfstab", "-U", mountpoint],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        error = result.stderr.strip() or "Unknown error."
        output_lines.append(f"[error] {error}")
        output_lines.append("")
        output_lines.append("[abort] System installation stopped.")
        return "\n".join(output_lines)

    fstab_content = result.stdout.strip()
    if not fstab_content:
        output_lines.append("[error] genfstab returned empty output.")
        output_lines.append("")
        output_lines.append("[abort] System installation stopped.")
        return "\n".join(output_lines)

    fstab_path.write_text(result.stdout, encoding="utf-8")

    output_lines.append(fstab_content)
    output_lines.append("")
    output_lines.append(
        "[ok] Base system installed with pacstrap "
        "(base linux linux-firmware iptables-nft)."
    )
    output_lines.append("[ok] fstab generated at /mnt/etc/fstab.")

    return "\n".join(output_lines)
