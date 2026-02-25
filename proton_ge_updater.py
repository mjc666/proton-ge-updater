#!/usr/bin/env python3
"""Check for and install the latest GloriousEggroll Proton-GE release."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

API_URL = "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest"
COMPAT_DIR = Path.home() / ".steam" / "steam" / "compatibilitytools.d"


def get_latest_release():
    """Fetch the latest release info from GitHub."""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "proton-ge-updater"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    tag = data["tag_name"]
    tarball_url = None
    checksum_url = None

    for asset in data["assets"]:
        name = asset["name"]
        if name.endswith(".tar.gz"):
            tarball_url = asset["browser_download_url"]
        elif name.endswith(".sha512sum"):
            checksum_url = asset["browser_download_url"]

    if not tarball_url:
        raise RuntimeError("No .tar.gz asset found in the latest release")

    return {"tag": tag, "tarball_url": tarball_url, "checksum_url": checksum_url}


def is_installed(tag):
    """Check if a version is already installed."""
    return (COMPAT_DIR / tag).is_dir()


def download_with_progress(url, dest):
    """Download a file with progress output."""
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(downloaded * 100 / total_size, 100)
            mb_down = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            sys.stdout.write(
                f"\r  Downloading: {mb_down:.1f}/{mb_total:.1f} MB ({percent:.0f}%)"
            )
            sys.stdout.flush()

    urllib.request.urlretrieve(url, dest, reporthook=progress_hook)
    print()


def verify_checksum(tar_path, checksum_url):
    """Verify the SHA-512 checksum of the downloaded tarball."""
    req = urllib.request.Request(checksum_url, headers={"User-Agent": "proton-ge-updater"})
    with urllib.request.urlopen(req) as resp:
        expected = resp.read().decode().split()[0]

    sha512 = hashlib.sha512()
    with open(tar_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            sha512.update(chunk)

    actual = sha512.hexdigest()
    if actual != expected:
        tar_path.unlink()
        raise RuntimeError(
            f"Checksum mismatch:\n  expected: {expected}\n  actual:   {actual}"
        )


def extract(tar_path):
    """Extract the tarball to the compatibility tools directory."""
    print(f"  Extracting to {COMPAT_DIR}/...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=COMPAT_DIR, filter="data")
    tar_path.unlink()


def version_key(name):
    """Extract (major, minor) tuple from a GE-Proton directory name for sorting."""
    match = re.match(r"GE-Proton(\d+)-(\d+)", name)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return (0, 0)


def cleanup_old_versions(keep=2, auto=False):
    """Remove old GE-Proton installs if there are more than `keep`."""
    ge_dirs = sorted(
        [d for d in COMPAT_DIR.iterdir() if d.is_dir() and d.name.startswith("GE-Proton")],
        key=lambda d: version_key(d.name),
        reverse=True,
    )

    if len(ge_dirs) <= keep:
        return

    to_remove = ge_dirs[keep:]
    print(f"\nFound {len(ge_dirs)} GE-Proton installs (keeping newest {keep}):")
    for d in ge_dirs[:keep]:
        print(f"  Keep:   {d.name}")
    for d in to_remove:
        print(f"  Remove: {d.name}")

    if not auto:
        answer = input("\nDelete old versions? [y/N] ").strip().lower()
        if answer != "y":
            print("  Skipped cleanup.")
            return

    for d in to_remove:
        shutil.rmtree(d)
        print(f"  Deleted {d.name}")


def send_notification(tag, email):
    """Send an email notification about the update via local sendmail."""
    message = (
        f"Subject: Proton GE updated to {tag}\n"
        f"To: {email}\n"
        f"\n"
        f"GE-Proton has been updated to {tag}.\n"
        f"Installed to: {COMPAT_DIR / tag}\n"
    )
    try:
        subprocess.run(
            ["sendmail", "-t"],
            input=message.encode(),
            check=True,
            timeout=30,
        )
        print(f"  Notification sent to {email}")
    except FileNotFoundError:
        print("  Warning: sendmail not found, skipping notification", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"  Warning: sendmail failed (exit {e.returncode}), skipping notification", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Check for and install the latest GE-Proton release")
    parser.add_argument("--auto", action="store_true", help="Run unattended (auto-cleanup, no prompts)")
    parser.add_argument("--email", metavar="ADDR", help="Send email notification on update")
    args = parser.parse_args()

    print("Proton GE Updater")
    print("=" * 40)

    print("Checking latest release...")
    release = get_latest_release()
    tag = release["tag"]
    print(f"  Latest: {tag}")

    if is_installed(tag):
        print(f"  {tag} is already installed. Nothing to do.")
    else:
        print(f"  {tag} not found locally. Installing...")

        COMPAT_DIR.mkdir(parents=True, exist_ok=True)
        tar_path = COMPAT_DIR / f"{tag}.tar.gz"

        download_with_progress(release["tarball_url"], tar_path)

        if release["checksum_url"]:
            print("  Verifying SHA-512 checksum...")
            verify_checksum(tar_path, release["checksum_url"])
            print("  Checksum OK.")

        extract(tar_path)
        print(f"  {tag} installed successfully.")

        if args.email:
            send_notification(tag, args.email)

    cleanup_old_versions(auto=args.auto)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
