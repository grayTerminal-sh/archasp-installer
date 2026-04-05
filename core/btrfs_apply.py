"""Apply Btrfs mount and subvolume operations for ArchASP."""

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


def build_btrfs_apply_commands(
    disk_name: str, scheme: str
) -> list[list[str]]:
    """Build commands for Btrfs subvolume creation and final mounts."""
    if scheme not in SUPPORTED_SCHEMES:
        raise ValueError(f"Unsupported partition scheme: {scheme}")

    btrfs_part = get_partition_path(disk_name, 2)
    efi_part = get_partition_path(disk_name, 1)

    commands: list[list[str]] = [
        ["mount", "-o", "subvolid=5", btrfs_part, "/mnt"],
        ["btrfs", "subvolume", "create", "/mnt/@"],
    ]

    if scheme in {"uefi-standard", "uefi-complete"}:
        commands.append(["btrfs", "subvolume", "create", "/mnt/@home"])

    if scheme == "uefi-complete":
        commands.append(["btrfs", "subvolume", "create", "/mnt/@snapshots"])

    commands.extend(
        [
            [
                "umount",
                "/mnt"
            ],
            [
                "mount",
                "-o",
                "subvol=@,compress=zstd:3,noatime",
                btrfs_part,
                "/mnt"
            ],
        ]
    )

    if scheme in {"uefi-standard", "uefi-complete"}:
        commands.extend(
            [
                [
                    "mkdir",
                    "-p",
                    "/mnt/home"
                ],
                [
                    "mount",
                    "-o",
                    "subvol=@home,compress=zstd:3,noatime",
                    btrfs_part,
                    "/mnt/home",
                ],
            ]
        )

    if scheme == "uefi-complete":
        commands.extend(
            [
                ["mkdir", "-p", "/mnt/.snapshots"],
                [
                    "mount",
                    "-o",
                    "subvol=@snapshots,compress=zstd:3,noatime",
                    btrfs_part,
                    "/mnt/.snapshots",
                ],
            ]
        )

    commands.extend(
        [
            [
                "mkdir",
                "-p",
                "/mnt/boot/efi"
            ],
            [
                "mount",
                efi_part,
                "/mnt/boot/efi"
            ],
        ]
    )

    return commands


def validate_btrfs_apply_inputs(
    disk_name: str, scheme: str
) -> str | None:
    """Validate disk name, scheme, and required partition paths."""
    if not disk_name:
        return "[error] No disk name provided."

    if scheme not in SUPPORTED_SCHEMES:
        return f"[error] Unsupported partition scheme: {scheme}"

    btrfs_part = Path(get_partition_path(disk_name, 2))
    efi_part = Path(get_partition_path(disk_name, 1))

    if not btrfs_part.exists():
        return f"[error] Missing Btrfs partition: {btrfs_part}"

    if not efi_part.exists():
        return f"[error] Missing EFI partition: {efi_part}"

    return None


def run_logged_command(
    command: list[str], output_lines: list[str]
) -> bool:
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
        output_lines.append("[abort] Btrfs layout application stopped.")
        return False

    if result.stderr.strip():
        output_lines.append(result.stderr.strip())
        output_lines.append("")

    return True


def cleanup_mountpoint(
    output_lines: list[str]
) -> bool:
    """Unmount /mnt recursively if it is already mounted."""
    check = subprocess.run(
        ["mountpoint", "-q", "/mnt"],
        capture_output=True,
        text=True,
    )

    if check.returncode != 0:
        output_lines.append("[info] /mnt is already clean.\n")
        return True

    return run_logged_command(["umount", "-R", "/mnt"], output_lines)


def append_success_summary(
    scheme: str, disk_name: str, output_lines: list[str]
) -> None:
    """Append the final success summary."""
    output_lines.append(
        f"[ok] Btrfs subvolume layout"
        f"successfully applied on /dev/{disk_name}."
    )
    output_lines.append("[ok] Root mounted at /mnt")

    if scheme in {"uefi-standard", "uefi-complete"}:
        output_lines.append("[ok] Home mounted at /mnt/home")

    if scheme == "uefi-complete":
        output_lines.append("[ok] Snapshots mounted at /mnt/.snapshots")

    output_lines.append("[ok] EFI mounted at /mnt/boot/efi")


def apply_btrfs_layout(
    disk_name: str, scheme: str
) -> str:
    """Apply the Btrfs subvolume and mount layout and return a terminal log."""
    error = validate_btrfs_apply_inputs(disk_name, scheme)
    if error:
        return error

    commands = build_btrfs_apply_commands(disk_name, scheme)
    output_lines: list[str] = []

    if not cleanup_mountpoint(output_lines):
        return "\n".join(output_lines)

    for command in commands:
        if not run_logged_command(command, output_lines):
            return "\n".join(output_lines)

    append_success_summary(scheme, disk_name, output_lines)

    return "\n".join(output_lines)
