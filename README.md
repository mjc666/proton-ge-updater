# Proton GE Updater

A single-file Python script that checks for the latest [GE-Proton](https://github.com/GloriousEggroll/proton-ge-custom) release and installs it to Steam's compatibility tools directory.

## Features

- Checks the latest release via GitHub API
- Skips download if already installed
- Verifies SHA-512 checksum before extracting
- Shows download progress
- Cleans up old versions (keeps newest 2)
- Unattended mode with email notifications
- No external dependencies (stdlib only)

## Usage

```bash
# Interactive
python3 proton_ge_updater.py

# Unattended (auto-cleanup, no prompts)
python3 proton_ge_updater.py --auto

# Unattended with email notification on update
python3 proton_ge_updater.py --auto --email your@email.com
```

Email is sent via local `sendmail` (works with msmtp, sendmail, or any local MTA).

## Automatic scheduling

Copy the systemd units and enable the timer to check for updates daily:

```bash
cp systemd/proton-ge-updater.service systemd/proton-ge-updater.timer ~/.config/systemd/user/
```

Edit the service to set your email address:

```bash
nano ~/.config/systemd/user/proton-ge-updater.service
```

Enable the timer:

```bash
systemctl --user daemon-reload
systemctl --user enable --now proton-ge-updater.timer
```

Check status:

```bash
systemctl --user status proton-ge-updater.timer
journalctl --user -u proton-ge-updater.service -f
```

## Requirements

- Python 3.12+
- Steam installed with the default compatibility tools directory (`~/.steam/steam/compatibilitytools.d/`)
- For email notifications: a local MTA (e.g. msmtp, sendmail)
