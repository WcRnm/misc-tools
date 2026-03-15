#!/usr/bin/env python3
import os
import time
import yaml
import argparse
import sys
import subprocess
import tarfile
import re

# 1. Versioning and Defaults
__version__ = "1.7.0"
DEFAULT_SETTINGS = os.path.join(os.path.expanduser("~"), "py-backup.yaml")

def resolve_smb_uri(uri):
    """
    Translates an smb://server/share/path URI into a
    local GVfs filesystem path for Linux.
    """
    if not uri or not uri.startswith("smb://"):
        return uri

    # Parse the URI: smb://[server]/[share]/[optional_path]
    match = re.match(r"smb://([^/]+)/([^/]+)(/.*)?", uri)
    if not match:
        print(f"Error: Could not parse SMB URI: {uri}")
        sys.exit(1)

    server, share, subpath = match.groups()
    subpath = subpath if subpath else ""
    uid = os.getuid()

    # Standard Linux GVfs path construction
    gvfs_path = f"/run/user/{uid}/gvfs/smb-share:server={server},share={share}{subpath}"

    if not os.path.exists(gvfs_path):
        print(f"Error: Remote share is not mounted.")
        print(f"Please open '{uri}' in your file manager (Nautilus/Dolphin) first.")
        sys.exit(1)

    return gvfs_path

def create_template(path):
    """Generates a sample YAML configuration file."""
    template = {
        "destination": "smb://zinc.local/backup/Computers/Cobalt",
        "sources": [
            os.path.join(os.path.expanduser("~"), "Documents"),
            os.path.join(os.path.expanduser("~"), "Projects")
        ]
    }
    try:
        with open(path, 'w') as f:
            yaml.dump(template, f, default_flow_style=False)
        print(f"--- Configuration Created ---")
        print(f"A template has been saved to: {path}")
    except Exception as e:
        print(f"Failed to create template: {e}")

def load_settings(config_path):
    """Loads configuration and handles template creation if missing."""
    if not os.path.exists(config_path):
        if config_path == DEFAULT_SETTINGS:
            create_template(config_path)
            sys.exit(0)
        else:
            print(f"Error: Specified config file '{config_path}' not found.")
            sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            if not data or 'destination' not in data or 'sources' not in data:
                print("Error: YAML must contain 'destination' and 'sources'.")
                sys.exit(1)
            return data
    except Exception as e:
        print(f"Error reading YAML: {e}")
        sys.exit(1)

def sync_folders(sources, destination):
    print("\n--- Operation 1: Syncing Latest Changes (rsync) ---")
    sync_root = os.path.join(destination, "latest_sync")

    for src in sources:
        if not os.path.exists(src):
            print(f"Skipping sync: {src} not found.")
            continue

        folder_name = os.path.basename(src.rstrip(os.sep))
        target_path = os.path.join(sync_root, folder_name)
        os.makedirs(target_path, exist_ok=True)

        print(f"Mirroring {folder_name}...")
        subprocess.run(["rsync", "-avz", "--delete", src.rstrip(os.sep) + "/", target_path + "/"], check=True)

def archive_folders(sources, destination):
    print("\n--- Operation 2: Creating Compressed Archive (tar.gz) ---")
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    archive_dir = os.path.join(destination, "archives")
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = os.path.join(archive_dir, f"backup_{timestamp}.tar.gz")

    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            for src in sources:
                if os.path.exists(src):
                    print(f"Compressing {src}...")
                    tar.add(src, arcname=os.path.basename(src))
        print(f"Archive created: {archive_path}")
    except Exception as e:
        print(f"Archive error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Professional Sync & Archive Tool.")
    parser.add_argument("-c", "--config", help="Path to custom YAML config")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    # 1. Determine and print the config path
    config_to_use = args.config if args.config else DEFAULT_SETTINGS
    abs_config_path = os.path.abspath(config_to_use)
    print(f"Using configuration file: {abs_config_path}")

    # 2. Load settings
    settings = load_settings(config_to_use)

    # 3. Resolve destination (Handles smb:// URIs)
    final_dest = resolve_smb_uri(settings['destination'])

    # 4. Final permission check
    if not os.access(final_dest, os.W_OK):
        print(f"Permission Error: Cannot write to {final_dest}.")
        sys.exit(1)

    # 5. Run operations
    sync_folders(settings['sources'], final_dest)
    archive_folders(settings['sources'], final_dest)
    print("\nBackup suite finished successfully.")

if __name__ == "__main__":
    main()