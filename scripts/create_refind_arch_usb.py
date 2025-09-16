#!/usr/bin/env python3
"""
Create Arch Linux USB with rEFInd boot manager for stubborn iMacs
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

def download_arch_iso():
    """Download latest Arch Linux ISO"""
    print_header("DOWNLOADING ARCH LINUX ISO")

    iso_url = "https://mirror.rackspace.com/archlinux/iso/latest/archlinux-x86_64.iso"
    iso_path = Path.home() / "Downloads" / "archlinux-x86_64.iso"

    if iso_path.exists():
        print(f"✅ ISO already exists: {iso_path}")
        return str(iso_path)

    print(f"📥 Downloading...")
    try:
        response = requests.get(iso_url, stream=True)
        response.raise_for_status()

        with open(iso_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"✅ Download complete: {iso_path}")
        return str(iso_path)

    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def create_emergency_usb():
    """Create USB with multiple boot options for stubborn hardware"""
    print_header("EMERGENCY USB CREATION")

    # Get USB device
    result = subprocess.run("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E '(disk|part)'",
                          shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("Available devices:")
        print(result.stdout)

    usb_device = input("Enter USB device (e.g., /dev/sdb): ").strip()

    if not usb_device.startswith('/dev/'):
        print("❌ Invalid device")
        return False

    print(f"⚠️  This will ERASE {usb_device}")
    confirm = input("Type 'YES': ")
    if confirm != "YES":
        return False

    # Download and flash with special parameters
    iso_path = download_arch_iso()
    if not iso_path:
        return False

    # Unmount
    subprocess.run(f"sudo umount {usb_device}* 2>/dev/null", shell=True)

    # Create with sync and special flags for old Macs
    dd_cmd = f"sudo dd if={iso_path} of={usb_device} bs=1M conv=sync status=progress"

    if run_command(dd_cmd, "Flashing with old Mac compatibility"):
        print(f"\n✅ Emergency USB created!")
        print(f"\n🔧 Try these boot options:")
        print(f"1. Hold 'C' key (CD boot mode)")
        print(f"2. Hold 'Option' then select USB")
        print(f"3. Hold 'Shift+Option+Command+R' (Internet Recovery)")

        return True

    return False

def main():
    print_header("EMERGENCY ARCH USB FOR STUBBORN iMAC")
    print("🆘 For iMacs that refuse to boot normally")
    print("📀 Uses old Mac boot compatibility methods")

    if create_emergency_usb():
        print(f"\n🎯 Boot Instructions:")
        print(f"1. Try holding 'C' key while booting (CD mode)")
        print(f"2. If that fails, try rEFInd method below")
    else:
        print("❌ Failed to create emergency USB")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n❌ Interrupted")
        sys.exit(1)