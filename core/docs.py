"""Markdown helpers for command explanations.

This module centralizes the explanatory texts displayed in the installer
UI. Each function returns Markdown content associated with one command
or one installation step.

Keeping these texts outside the widgets makes the interface code easier
to read and simplifies future translation or documentation work.
"""


def lsblk_explanation(selected_disk: str) -> str:
    """Return a Markdown explanation for the lsblk inspection command."""
    return (
        "## `lsblk`\n\n"
        "This command lists **block devices** available on the system.\n\n"
        "### Why we use it\n"
        "- To see available disks\n"
        "- To inspect partitions\n"
        "- To understand mount points before installation\n\n"
        "### Options used\n"
        "- `-o` selects displayed columns\n\n"
        "### Columns shown\n"
        "- `NAME`: device name\n"
        "- `SIZE`: device size\n"
        "- `TYPE`: disk or partition\n"
        "- `MOUNTPOINT`: where it is mounted\n\n"
        "### Executed command\n"
        "```bash\n"
        f"lsblk /dev/{selected_disk} -o NAME,SIZE,TYPE,MOUNTPOINT\n"
        "```"
    )
