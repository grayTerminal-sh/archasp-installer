"""Markdown helpers for command explanations.

This module centralizes the explanatory texts displayed in the installer
UI. Each function returns Markdown content associated with one command
or one installation step.

Keeping these texts outside the widgets makes the interface code easier
to read and simplifies future translation or documentation work.
"""


def preflight_explanation(keymap: str, network_mode: str) -> str:
    """Return a Markdown explanation for the live environment setup step."""
    network_label = (
        "Wi-Fi help with `iwctl`"
        if network_mode == "iwctl"
        else "Internet connection already available"
    )

    return (
        "## Live environment setup\n\n"
        "Before disk operations, the installer checks"
        "the live session setup.\n\n"
        "### Keyboard layout\n"
        f"- Selected keymap: `{keymap}`\n"
        f"- Command to apply: `loadkeys {keymap}`\n"
        "- This command affects the live Linux console of the machine\n"
        "- If you are connected through SSH, your local"
        "keyboard layout does not change\n\n"
        "### Network\n"
        f"- Selected mode: {network_label}\n\n"
        "If Wi-Fi is needed, Arch ISO typically uses `iwctl` to scan and "
        "connect to a wireless network.\n\n"
        "### Notes\n"
        "- This step is non-destructive\n"
        "- It prepares the live session before storage changes\n"
        "- You can continue once keyboard and internet access are ready"
    )


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


def btrfs_explanation() -> str:
    """Return a Markdown explanation for the Btrfs filesystem choice."""
    return (
        "## Btrfs filesystem\n\n"
        "The installer uses **Btrfs**"
        "as the default filesystem for the system "
        "partition.\n\n"
        "### Why Btrfs\n"
        "- Snapshots at the subvolume level,"
        "useful for safe upgrades and rollbacks\n"
        "- Checksums for data and metadata to detect silent corruption\n"
        "- Transparent compression to save space and reduce SSD wear\n"
        "- Flexible layout with subvolumes instead of many"
        "separate partitions\n\n"
        "### Layout used by this installer\n"
        "- One Btrfs partition for the system data\n"
        "- Subvolume `@` mounted as `/`\n"
        "- Subvolume `@home` mounted as `/home`\n"
        "- Subvolume `@snapshots` mounted as `/.snapshots`\n\n"
        "This layout follows a \"flat\" Btrfs structure:"
        "the top-level subvolume "
        "is used only to manage subvolumes,"
        "while the actual root filesystem is "
        "a dedicated subvolume.\n\n"
        "### Mount options\n"
        "- `compress=zstd` for transparent compression\n"
        "- `noatime` to avoid unnecessary write operations\n\n"
        "These defaults aim for a good balance between safety,"
        "performance, and ease of administration.\n"
    )
