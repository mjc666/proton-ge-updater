# Proton GE Updater

A single-file Python script that checks for the latest [GE-Proton](https://github.com/GloriousEggroll/proton-ge-custom) release and installs it to Steam's compatibility tools directory.

## Features

- Checks the latest release via GitHub API
- Skips download if already installed
- Verifies SHA-512 checksum before extracting
- Shows download progress
- No external dependencies (stdlib only)

## Usage

```bash
python3 proton_ge_updater.py
```

Or make it executable:

```bash
chmod +x proton_ge_updater.py
./proton_ge_updater.py
```

## Requirements

- Python 3.12+
- Steam installed with the default compatibility tools directory (`~/.steam/steam/compatibilitytools.d/`)
