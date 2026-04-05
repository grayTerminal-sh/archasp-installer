"""Apply destructive partitioning operations for ArchASP."""

from __future__ import annotations

from pathlib import Path
import subprocess


SUPPORTED_SCHEMES = {
    "uefi-simple",
    "uefi-standard",
    "uefi-complete",
}


def get_partition_path(
    disk_name: str, partition_number: int
) -> str:
    """Return the full partition path for a Linux block device."""
    base = f"/dev/{disk_name}"

    if disk_name.startswith(("nvme", "mmcblk")):
        return f"{base}p{partition_number}"

    return f"{base}{partition_number}"


def cleanup_mountpoint(output_lines: list[str]) -> bool:
    """Unmount /mnt recursively if it is already mounted."""
    check = subprocess.run(
        ["mountpoint", "-q", "/mnt"],
        capture_output=True,
        text=True,
    )

    if check.returncode != 0:
        output_lines.append("[info] /mnt is already clean.\n")
        return True

    output_lines.append("root@archiso# umount -R /mnt\n")

    result = subprocess.run(
        ["umount", "-R", "/mnt"],
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
        output_lines.append("[abort] Partition layout application stopped.")
        return False

    if result.stderr.strip():
        output_lines.append(result.stderr.strip())
        output_lines.append("")

    return True


def build_partition_commands(
    disk_name: str, scheme: str
) -> list[list[str]]:
    """Build the command list required"
    "to apply a supported partition layout."""
    if scheme not in SUPPORTED_SCHEMES:
        raise ValueError(f"Unsupported partition scheme: {scheme}")

    disk_path = f"/dev/{disk_name}"
    efi_part = get_partition_path(disk_name, 1)
    btrfs_part = get_partition_path(disk_name, 2)

    return [
        [
            "sgdisk",
            "--zap-all",
            disk_path
        ],
        [
            "sgdisk",
            "-o",
            disk_path
        ],
        [
            "sgdisk",
            "-n",
            "1:0:+512MiB",
            "-t",
            "1:EF00",
            "-c",
            "1:EFI",
            disk_path
        ],
        [
            "sgdisk",
            "-n",
            "2:0:0",
            "-t",
            "2:8300",
            "-c",
            "2:ARCH_BTRFS",
            disk_path
        ],
        [
            "partprobe",
            disk_path
        ],
        [
            "mkfs.fat",
            "-F32",
            efi_part
        ],
        [
            "mkfs.btrfs",
            "-f",
            btrfs_part
        ],
    ]


def apply_partition_layout(
    disk_name: str, scheme: str
) -> str:
    """Cleanup mount point and apply the selected partition
    layout and return a terminal-style log."""
    if not disk_name:
        return "[error] No disk name provided."

    disk_path = Path(f"/dev/{disk_name}")

    if not disk_path.exists():
        return f"[error] Target disk does not exist: {disk_path}"

    try:
        commands = build_partition_commands(disk_name, scheme)
    except ValueError as error:
        return f"[error] {error}"

    output_lines: list[str] = []

    if not cleanup_mountpoint(output_lines):
        return "\n".join(output_lines)

    for command in commands:
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
            output_lines.append(
                "[abort] Partition layout application stopped."
            )
            return "\n".join(output_lines)

        if result.stderr.strip():
            output_lines.append(result.stderr.strip())
            output_lines.append("")

    output_lines.append(
        f"[ok] Partition layout successfully"
        f"applied on {disk_path}."
    )
    output_lines.append(
        f"[ok] EFI partition created at {get_partition_path(disk_name, 1)}."
    )
    output_lines.append(
        f"[ok] Btrfs partition created at {get_partition_path(disk_name, 2)}."
    )

    return "\n".join(output_lines)
