"""Helpers for partition layout simulation.

This module contains the non-destructive logic used to build partition
plans from a selected disk size and a chosen installation scheme.

The functions in this module do not write anything to disk. They only
compute a preview that can later be reviewed and confirmed by the user.
"""

from dataclasses import dataclass


MIB = 1024 * 1024
GIB = 1024 * 1024 * 1024


@dataclass
class PartitionPlanItem:
    """Represent one partition entry in a simulated layout."""

    name: str
    size_bytes: int
    fs_type: str
    mountpoint: str


def format_size(size_bytes: int) -> str:
    """Convert a size in bytes to a human-readable string."""
    gib = size_bytes / GIB
    if gib >= 1:
        return f"{gib:.1f} GiB"

    mib = size_bytes / MIB
    return f"{mib:.0f} MiB"


def simulate_partition_layout(
    disk_size_bytes: int,
    scheme: str
) -> list[PartitionPlanItem]:
    """Build a simulated partition layout for a selected scheme.

    Supported schemes:
    - ``uefi-simple``: EFI + root
    - ``uefi-standard``: EFI + swap + root
    - ``uefi-complete``: EFI + swap + root + home
    - ``manual``: no automatic plan
    """
    efi_size = 512 * MIB
    swap_size = 2 * GIB
    home_size = 20 * GIB

    if disk_size_bytes <= efi_size:
        return []

    if scheme == "uefi-simple":
        root_size = disk_size_bytes - efi_size
        return [
            PartitionPlanItem("EFI", efi_size, "fat32", "/boot/efi"),
            PartitionPlanItem("root", root_size, "ext4", "/"),
        ]

    if scheme == "uefi-standard":
        root_size = disk_size_bytes - efi_size - swap_size
        if root_size <= 0:
            return []

        return [
            PartitionPlanItem("EFI", efi_size, "fat32", "/boot/efi"),
            PartitionPlanItem("swap", swap_size, "linux-swap", "swap"),
            PartitionPlanItem("root", root_size, "ext4", "/"),
        ]

    if scheme == "uefi-complete":
        root_size = disk_size_bytes - efi_size - swap_size - home_size
        if root_size <= 0:
            return []

        return [
            PartitionPlanItem("EFI", efi_size, "fat32", "/boot/efi"),
            PartitionPlanItem("swap", swap_size, "linux-swap", "swap"),
            PartitionPlanItem("root", root_size, "ext4", "/"),
            PartitionPlanItem("home", home_size, "ext4", "/home"),
        ]

    return []


def render_partition_plan(
    disk_name: str,
    disk_size_bytes: int,
    scheme: str,
    plan: list[PartitionPlanItem]
) -> str:
    """Render a simulated partition plan as Markdown text."""
    if scheme == "manual":
        return (
            f"## Partition simulation for /dev/{disk_name}\n\n"
            "Mode: manual\n\n"
            "No automatic partition plan generated.\n"
            "You will define partitions manually in the next step."
        )

    if not plan:
        return (
            f"## Partition simulation for /dev/{disk_name}\n\n"
            f"Selected scheme: {scheme}\n\n"
            "Unable to generate a valid partition layout for this disk size."
        )

    lines = [
        f"## Partition simulation for /dev/{disk_name}",
        "",
        f"Disk size: {format_size(disk_size_bytes)}",
        f"Selected scheme: {scheme}",
        "",
        "| Partition | Size | FS | Mount |",
        "|---|---:|---|---|",
    ]

    for item in plan:
        lines.append(
            f"| {item.name} | {format_size(item.size_bytes)} | "
            f"{item.fs_type} | {item.mountpoint} |"
        )

    lines.append("")
    lines.append("No change has been applied yet.")
    return "\n".join(lines)
