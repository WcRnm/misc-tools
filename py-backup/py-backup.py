#!/usr/bin/env python3
import os
import time
import yaml
import argparse
import sys
import subprocess
import tarfile

# 1. Versioning and Defaults
__version__ = "1.5.0"
DEFAULT_SETTINGS = os.path.join(os.path.expanduser("~"), "py-backup.yaml")

def load_settings(config_path):
    """Loads configuration and handles template creation if missing."""
    if not os.path.exists(config_path):
        if config_path == DEFAULT_SETTINGS:
            create_template(config_path)
            sys.exit(0) # Exit so the user can edit the new file
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

def create_template(path):
    """Generates a sample YAML configuration file."""
    template = {
        "destination": "/mnt/zinc_backup/Computers/Cobalt",
        "sources": [
            "/home/user/Documents",
            "/home/user/Projects"
        ]
    }
    try:
        with open(path, 'w') as f:
            yaml.dump(template, f, default_flow_style=False)
        print(f"--- Configuration Created ---")
        print(f"A template has been saved to: {path}")
        print(f"Please edit this file with your actual paths and run the script again.")
    except Exception as e:
        print(f"Failed to create template: {e}")

def sync_folders(sources, destination):
    """Uses rsync to mirror folders (Latest Sync)."""
    print("\n--- Operation 1: Syncing Latest Changes ---")
    sync_root = os.path.join(destination, "latest_sync")

    for src in sources:
        if not os.path.exists(src):
            print(f"Skipping sync: {src} not found.")
            continue

        folder_name = os.path.basename(src.rstrip(os.sep))
        target_path = os.path.join(sync_root, folder_name)
        os.makedirs(target_path, exist_ok=True)

        print(f"Mirroring {folder_name}...")
        # -a: archive, -v: verbose, -z: compress transfer, --delete: mirror exactly
        # Trailing slashes on src ensure we copy contents into the target_path
        subprocess.run(["rsync", "-avz", "--delete", src.rstrip(os.sep) + "/", target_path + "/"], check=True)

def archive_folders(sources, destination):
    """Creates a timestamped .tar.gz archive."""
    print("\n--- Operation 2: Creating Compressed Archive ---")
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

    config_to_use = args.config if args.config else DEFAULT_SETTINGS
    settings = load_settings(config_to_use)

    srcs = settings['sources']
    dest = settings['destination']

    # Final permission check for your SMB mount
    if not os.access(dest, os.W_OK):
        print(f"Permission Error: Cannot write to {dest}.")
        print("Ensure your SMB mount includes 'uid' and 'gid' in the mount options.")
        sys.exit(1)

    sync_folders(srcs, dest)
    archive_folders(srcs, dest)
    print("\nBackup suite finished successfully.")

if __name__ == "__main__":
    main()
