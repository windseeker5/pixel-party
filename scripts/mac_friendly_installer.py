#!/usr/bin/env python3
"""
Mac-Friendly Linux Installer Script
Downloads and flashes Mac-compatible Linux distributions
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

def print_header(text):
    print(f"\n{'='*50}")
    print(f" {text}")
    print(f"{'='*50}")

def run_command(cmd, description):
    """Run shell command with error handling"""
    print(f"\n🔧 {description}")
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(f"✅ Success: {description}")
    return True

def download_file(url, filename):
    """Download file with progress"""
    filepath = Path.home() / "Downloads" / filename

    if filepath.exists():
        print(f"✅ File already exists: {filepath}")
        return str(filepath)

    print(f"📥 Downloading: {filename}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r📊 Progress: {percent:.1f}%", end="", flush=True)

        print(f"\n✅ Download complete: {filepath}")
        return str(filepath)

    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def choose_distribution():
    """Let user choose Linux distribution"""
    print_header("CHOOSE MAC-FRIENDLY LINUX DISTRIBUTION")

    distributions = {
        "1": {
            "name": "Ubuntu 24.04 LTS",
            "url": "https://releases.ubuntu.com/24.04/ubuntu-24.04.3-desktop-amd64.iso",
            "filename": "ubuntu-24.04.3-desktop-amd64.iso",
            "description": "Most popular, excellent hardware detection"
        },
        "2": {
            "name": "Linux Mint 22 Cinnamon",
            "url": "https://mirrors.edge.kernel.org/linuxmint/stable/22/linuxmint-22-cinnamon-64bit.iso",
            "filename": "linuxmint-22-cinnamon-64bit.iso",
            "description": "Mac-like interface, very user friendly"
        },
        "3": {
            "name": "Pop!_OS 22.04",
            "url": "https://iso.pop-os.org/22.04/amd64/intel/45/pop-os_22.04_amd64_intel_45.iso",
            "filename": "pop-os_22.04_amd64_intel_45.iso",
            "description": "Optimized graphics drivers, great for gaming"
        }
    }

    for key, distro in distributions.items():
        print(f"{key}. {distro['name']}")
        print(f"   {distro['description']}")

    while True:
        choice = input(f"\nChoose distribution (1-3): ").strip()
        if choice in distributions:
            return distributions[choice]
        print("❌ Invalid choice. Please enter 1, 2, or 3.")

def list_usb_devices():
    """List available USB devices"""
    print_header("USB DEVICES")
    result = subprocess.run("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E '(disk|part)'",
                          shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("Available storage devices:")
        print(result.stdout)
        return True
    else:
        print("❌ Could not list devices")
        return False

def flash_usb(iso_path, usb_device):
    """Flash ISO to USB device"""
    print_header("FLASHING USB DRIVE")

    if not os.path.exists(usb_device):
        print(f"❌ Device {usb_device} not found!")
        return False

    print(f"⚠️  WARNING: This will ERASE ALL DATA on {usb_device}")
    confirm = input("Type 'YES' to continue: ")
    if confirm != "YES":
        print("❌ Aborted by user")
        return False

    # Unmount device
    subprocess.run(f"sudo umount {usb_device}* 2>/dev/null", shell=True)

    # Flash with balenaetcher-like command (using dd)
    dd_cmd = f"sudo dd if={iso_path} of={usb_device} bs=4M status=progress oflag=sync"
    return run_command(dd_cmd, f"Flashing {iso_path} to {usb_device}")

def show_mac_instructions():
    """Show Mac boot instructions"""
    print_header("iMAC BOOT INSTRUCTIONS")

    instructions = [
        "🔌 Plug USB into iMac + ethernet cable",
        "⌥  Hold Option/Alt key while powering on",
        "💾 Select USB/EFI Boot (NOT macOS)",
        "🎯 These should boot without black screens!"
    ]

    for i, instruction in enumerate(instructions, 1):
        print(f"{i}. {instruction}")

    print(f"\n✨ Why these work better:")
    print(f"   • Ubuntu/Mint have better Intel Mac drivers")
    print(f"   • Pop!_OS includes graphics fixes")
    print(f"   • All are tested on Mac hardware")

def main():
    print_header("MAC-FRIENDLY LINUX INSTALLER")
    print("🍎 This script downloads Linux distributions that work well on Intel Macs")
    print("💡 These should boot without the black screen issues you experienced")

    # Choose distribution
    distro = choose_distribution()

    # Download ISO
    iso_path = download_file(distro["url"], distro["filename"])
    if not iso_path:
        print("❌ Failed to download ISO")
        sys.exit(1)

    # List USB devices
    if not list_usb_devices():
        print("❌ Could not list USB devices")
        sys.exit(1)

    # Get USB device
    print(f"\n⚠️  WARNING: Choose carefully! Wrong device = data loss!")
    usb_device = input("Enter USB device (e.g., /dev/sdb): ").strip()

    if not usb_device.startswith('/dev/'):
        print("❌ Invalid device path")
        sys.exit(1)

    # Flash USB
    if flash_usb(iso_path, usb_device):
        print(f"\n✅ {distro['name']} USB ready!")
        show_mac_instructions()
        print(f"\n🎉 This should work much better on your iMac!")
    else:
        print("❌ Failed to flash USB drive")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)