# ArchASP Installer

ArchASP is a Textual-based terminal installer assistant for Arch Linux.

The project aims to provide a guided, readable, and shareable interface
for installation steps such as disk selection, partition planning,
formatting, mounting, and system bootstrap.

## Status

This project is currently in active development.

Implemented or started:
- Disk detection
- Disk inspection with `lsblk`
- Partitioning step structure
- Partition layout simulation
- Shared command explanation panel
- Modular Textual widget architecture

Planned next:
- Partition confirmation
- Real partition application
- Filesystem formatting
- Mounting
- Pacstrap and base install
- Post-install configuration

## Goals

- Build a clean and understandable Arch Linux installer assistant
- Keep the UI modular and easy to maintain
- Separate UI code from system logic
- Make the codebase easy to read, share, and contribute to
- Add safety steps before destructive actions

## Tech stack

- Python
- Textual
- `lsblk`
- `subprocess`
- Markdown-based UI explanations

## Current features

### Disk selection
The installer can detect available disks and display useful metadata such
as size, model, and transport type.

### Disk inspection
Once a disk is selected, the app runs `lsblk` and displays both a command
explanation and a terminal-like output preview.

### Partition simulation
The partitioning step can simulate predefined layouts before any real
change is applied to the disk.

Supported simulation modes:
- UEFI simple: EFI + root
- UEFI standard: EFI + swap + root
- UEFI complete: EFI + swap + root + home
- Manual

## Safety

At the current stage, the project mainly focuses on read-only inspection
and partition layout simulation.

Partition simulation does **not** write to disk.

Any future destructive action should be preceded by:
- a preview,
- a confirmation step,
- explicit user validation.

## Project structure

```text
.
├── main.py
├── style.tcss
├── core/
│   ├── disks.py
│   ├── docs.py
│   └── partitioning.py
└── ui/
    ├── choose_disk.py
    ├── command_view.py
    └── partition_disk.py
```

## Architecture

The application follows a modular Textual design:

- `main.py` orchestrates the application
- `ui/` contains Textual widgets
- `core/` contains helper logic and command wrappers
- widgets communicate with the main app through Textual messages

This separation helps keep the interface readable and makes the project
easier to extend step by step.

## Installation

Clone the repository:

```bash
git clone <your-repository-url>
cd archasp
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install textual
```

## Run

Start the application with:

```bash
python main.py
```

## Development notes

This project is being built progressively, with an emphasis on:
- code readability,
- modular widgets,
- internal documentation,
- safe step-by-step implementation.

The current codebase is intentionally organized early to make future
sharing and open-source collaboration easier.

## Roadmap

- [x] Detect disks
- [x] Inspect selected disk
- [x] Add command explanation panel
- [x] Start partitioning step
- [x] Simulate partition layouts
- [ ] Add partition confirmation
- [ ] Apply partition plan
- [ ] Format partitions
- [ ] Mount target filesystem
- [ ] Install base system
- [ ] Configure bootloader
- [ ] Add post-install setup helpers

## Contributing

Contributions, feedback, cleanup suggestions, and architecture ideas are
welcome.

For now, the easiest way to contribute is to:
- report bugs,
- suggest UI improvements,
- improve documentation,
- propose safer installation flows.

## License

License to be defined.
