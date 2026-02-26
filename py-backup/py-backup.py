#!/usr/bin/env python3
import os
import shutil
import time
import yaml
import argparse
import sys

# 1. Versioning
__version__ = "1.3.0"

# Default settings path in user's home directory
DEFAULT_SETTINGS = os.path.join(os.path.expanduser("~"), "py-backup.yaml")

def load_settings(config_path):
    """Loads configuration from a YAML file."""
    if not os.path.exists(config_path):
        # Create a template if the default file doesn't exist
        if config_path == DEFAULT_SETTINGS:
            create_template(config_path)
            print(f"Created a template config at {config_path}. Please edit it and run again.")
            sys.exit(0)
        else:
            print(f"Error: Configuration file '{config_path}' not found.")
            sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            # Basic validation of the YAML structure
            if not data or 'destination' not in data or 'sources' not in data:
                print("Error: YAML must contain 'destination' and 'sources' list.")
                sys.exit(1)
            return data
    except Exception as e:
        print(f"Error reading YAML: {e}")
        sys.exit(1)

def create_template(path):
    """Creates a sample YAML file for the user."""
    template = {
        "destination": "/path/to/backup/folder",
        "sources": [
            "/path/to/documents",
            "/path/to/projects"
        ]
    }
    with open(path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False)

def run_backup(sources, destination):
    """Iterates through all sources and backs them up to a timestamped folder."""
    if not os.path.exists(destination):
        print(f"Error: Destination '{destination}' does not exist.")
        return

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    backup_root = os.path.join(destination, f'backup_{timestamp}')

    try:
        os.makedirs(backup_root, exist_ok=True)
        print(f"Starting backup to: {backup_root}")

        for src in sources:
            if not os.path.exists(src):
                print(f"Skipping: Source '{src}' not found.")
                continue

            # Get the folder name to avoid collisions in the backup root
            folder_name = os.path.basename(src.rstrip(os.sep))
            target_path = os.path.join(backup_root, folder_name)

            print(f"  -> Copying {src}...")
            if os.path.isdir(src):
                shutil.copytree(src, target_path)
            else:
                shutil.copy2(src, target_path)

        print("Backup process finished successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description="Multi-source YAML-based backup utility.")
    parser.add_argument("-c", "--config", help="Path to a custom YAML settings file")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    # Determine which config file to use
    config_to_use = args.config if args.config else DEFAULT_SETTINGS

    # Load settings
    settings = load_settings(config_to_use)

    # Execute backup
    run_backup(settings['sources'], settings['destination'])

if __name__ == "__main__":
    main()
