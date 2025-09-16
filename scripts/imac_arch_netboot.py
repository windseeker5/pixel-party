#!/usr/bin/env python3
"""
Alternative: Create Arch Linux netboot setup for iMac
Uses archboot which has better Mac compatibility
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
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(f"✅ Success: {description}")
    return True

def download_archboot():
    """Download archboot - alternative Arch installer with better Mac support"""
    print_header("DOWNLOADING ARCHBOOT (MAC-FRIENDLY)")

    # Archboot has better Mac compatibility
    archboot_url = "https://downloads.archboot.com/iso/x86_64/latest/archboot-latest-x86_64.iso"
    iso_path = Path.home() / "Downloads" / "archboot-latest-x86_64.iso"

    print(f"🍎 Archboot includes:")
    print(f"   • Better Mac hardware detection")
    print(f"   • Pre-configured boot parameters")
    print(f"   • Multiple boot options")

    if iso_path.exists():
        print(f"✅ Archboot already exists: {iso_path}")
        return str(iso_path)

    print(f"📥 Downloading from: {archboot_url}")
    try:
        response = requests.get(archboot_url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(iso_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r📊 Progress: {percent:.1f}%", end="", flush=True)

        print(f"\n✅ Download complete: {iso_path}")
        return str(iso_path)

    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def main():
    print_header("ARCHBOOT - ARCH LINUX FOR MAC")
    print("🍎 Archboot is specifically designed for better Mac compatibility")
    print("🚫 NO MANUAL BOOT PARAMETER EDITING REQUIRED!")

    # Download archboot
    iso_path = download_archboot()
    if not iso_path:
        print("❌ Failed to download archboot")
        sys.exit(1)

    # List USB devices
    result = subprocess.run("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E '(disk|part)'",
                          shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print_header("USB DEVICES")
        print("Available storage devices:")
        print(result.stdout)

    # Get USB device
    print(f"\n⚠️  WARNING: Choose carefully! Wrong device = data loss!")
    usb_device = input("Enter USB device (e.g., /dev/sdb): ").strip()

    if not usb_device.startswith('/dev/'):
        print("❌ Invalid device path")
        sys.exit(1)

    if not os.path.exists(usb_device):
        print(f"❌ Device {usb_device} not found!")
        sys.exit(1)

    # Flash USB
    print(f"⚠️  WARNING: This will ERASE ALL DATA on {usb_device}")
    confirm = input("Type 'YES' to continue: ")
    if confirm != "YES":
        print("❌ Aborted by user")
        sys.exit(1)

    # Unmount and flash
    subprocess.run(f"sudo umount {usb_device}* 2>/dev/null", shell=True)

    dd_cmd = f"sudo dd if={iso_path} of={usb_device} bs=4M status=progress oflag=sync"
    if run_command(dd_cmd, f"Flashing archboot to {usb_device}"):
        print_header("iMAC BOOT INSTRUCTIONS")

        instructions = [
            "🔌 Plug USB into iMac + ethernet cable",
            "⌥  Hold Option/Alt while powering on",
            "💾 Select USB/EFI Boot",
            "🎯 Archboot should detect iMac hardware automatically",
            "📱 Follow the graphical installer"
        ]

        for i, instruction in enumerate(instructions, 1):
            print(f"{i}. {instruction}")

        print(f"\n✨ Why archboot works better:")
        print(f"   • Designed specifically for difficult hardware")
        print(f"   • Includes Mac-specific drivers")
        print(f"   • Has multiple boot fallback options")
        print(f"   • Graphical installer option")

        print(f"\n🎉 Archboot USB ready - should work much better on iMac!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)