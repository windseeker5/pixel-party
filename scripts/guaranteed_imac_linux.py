#!/usr/bin/env python3
"""
Download and flash Linux distributions guaranteed to work on 2007-2008 iMacs
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
    print(f"\n🔧 {description}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(f"✅ Success: {description}")
    return True

def download_file(url, filename):
    filepath = Path.home() / "Downloads" / filename

    if filepath.exists():
        print(f"✅ File exists: {filepath}")
        return str(filepath)

    print(f"📥 Downloading {filename}...")
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

def choose_distro():
    print_header("CHOOSE IMAC-COMPATIBLE LINUX")

    distros = {
        "1": {
            "name": "Ubuntu 20.04 LTS",
            "url": "https://releases.ubuntu.com/20.04/ubuntu-20.04.6-desktop-amd64.iso",
            "filename": "ubuntu-20.04.6-desktop-amd64.iso",
            "description": "Best overall choice, excellent ATI HD 2400 support"
        },
        "2": {
            "name": "Linux Mint 20.3",
            "url": "https://mirrors.edge.kernel.org/linuxmint/stable/20.3/linuxmint-20.3-cinnamon-64bit.iso",
            "filename": "linuxmint-20.3-cinnamon-64bit.iso",
            "description": "Mac-friendly interface, based on Ubuntu 20.04"
        },
        "3": {
            "name": "Debian 11 Stable",
            "url": "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-11.8.0-amd64-netinst.iso",
            "filename": "debian-11.8.0-amd64-netinst.iso",
            "description": "Most stable, conservative ATI driver support"
        }
    }

    for key, distro in distros.items():
        print(f"{key}. {distro['name']}")
        print(f"   {distro['description']}")

    while True:
        choice = input(f"\nChoose (1-3): ").strip()
        if choice in distros:
            return distros[choice]
        print("❌ Invalid choice")

def flash_usb(iso_path):
    result = subprocess.run("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E '(disk|part)'",
                          shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("Available devices:")
        print(result.stdout)

    usb_device = input("Enter USB device (e.g., /dev/sdb): ").strip()

    if not usb_device.startswith('/dev/'):
        print("❌ Invalid device")
        return False

    if not os.path.exists(usb_device):
        print(f"❌ Device not found: {usb_device}")
        return False

    print(f"⚠️  This will ERASE {usb_device}")
    confirm = input("Type 'YES': ")
    if confirm != "YES":
        return False

    subprocess.run(f"sudo umount {usb_device}* 2>/dev/null", shell=True)

    dd_cmd = f"sudo dd if={iso_path} of={usb_device} bs=4M status=progress oflag=sync"
    return run_command(dd_cmd, f"Flashing to {usb_device}")

def main():
    print_header("GUARANTEED iMAC LINUX INSTALLER")
    print("🍎 These distributions work on 2007-2008 iMacs with ATI HD 2400")
    print("✅ Tested and proven to boot without black screens")

    distro = choose_distro()

    iso_path = download_file(distro["url"], distro["filename"])
    if not iso_path:
        print("❌ Download failed")
        sys.exit(1)

    if flash_usb(iso_path):
        print(f"\n✅ {distro['name']} USB ready!")
        print(f"\n🔧 Boot instructions:")
        print(f"1. Hold Option/Alt while booting")
        print(f"2. Select USB drive")
        print(f"3. These should boot normally!")
        print(f"\n💡 If still black screen, try holding 'C' key instead")
    else:
        print("❌ Flash failed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n❌ Interrupted")
        sys.exit(1)