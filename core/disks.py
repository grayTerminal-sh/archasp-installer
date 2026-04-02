"""Helpers for disk discovery and inspection.

This module wraps read-only system commands used by the installer to:
- list available block devices,
- format disk information for display,
- inspect a selected disk,
- retrieve exact disk size for partition simulation.

All functions in this module are non-destructive. They only read
system information from lsblk.
"""

import json
import subprocess
from typing import Any


def detect_disks() -> list[dict[str, Any]]:
    """Detect available block devices and return disk-level entries only.

    The returned list is normalized for UI usage and contains only
    devices whose type is reported as ``disk`` by lsblk.
    """
    result = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MODEL,TRAN"],
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)
    disks = []

    for device in data["blockdevices"]:
        if device["type"] == "disk":
            disks.append({
                "name": device.get("name", "unknown"),
                "size": device.get("size", "unknown"),
                "model": device.get("model") or "unknown model",
                "tran": device.get("tran") or "unknown tran",
            })

    return disks


def format_disks(
    disks: list[dict[str, Any]]
) -> str:
    """Format detected disks as a human-readable multiline string."""
    if not disks:
        return "No disks detected."

    lines = ["Disks detected:"]

    for disk in disks:
        lines.append(
            f"- {disk['name']} | {disk['size']} | "
            f"{disk['model']} | {disk['tran']}"
        )

    return "\n".join(lines)


def inspect_disk(
    disk_name: str
) -> str:
    """Inspect a selected disk with lsblk and return terminal-like output."""
    command = [
        "lsblk",
        f"/dev/{disk_name}",
        "-o",
        "NAME,SIZE,TYPE,MOUNTPOINT",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    output = result.stdout.strip()
    error = result.stderr.strip()

    content = (
        f"root@archiso# lsblk /dev/{disk_name} "
        f"-o NAME,SIZE,TYPE,MOUNTPOINT\n\n"
    )

    if output:
        content += output

    if error:
        content += f"\n\n[stderr]\n{error}"

    return content


def get_disk_size_bytes(
    disk_name: str
) -> int:
    """Return the exact size of a disk in bytes.

    This function is used by the partition simulation step to compute
    partition layouts from the selected target disk.
    """
    result = subprocess.run(
        [
            "lsblk",
            "--json",
            "--bytes",
            "--nodeps",
            "--output",
            "NAME,SIZE,TYPE",
            f"/dev/{disk_name}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    devices = data.get("blockdevices", [])

    if not devices:
        raise ValueError(f"Disk /dev/{disk_name} not found.")

    device = devices[0]

    if device.get("type") != "disk":
        raise ValueError(f"/dev/{disk_name} is not a disk.")

    size = device.get("size")

    if size is None:
        raise ValueError(f"Unable to read size for /dev/{disk_name}.")

    return int(size)
