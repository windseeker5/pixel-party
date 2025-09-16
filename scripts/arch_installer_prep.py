#!/usr/bin/env python3
"""
Arch Linux USB Installer Preparation Script
Automates downloading Arch ISO and flashing to USB drive
"""

import os
import sys
import subprocess
import requests
from pathlib import Path
import time

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

def download_arch_iso():
    """Download latest Arch Linux ISO"""
    print_header("DOWNLOADING ARCH LINUX ISO")

    iso_url = "https://mirror.rackspace.com/archlinux/iso/latest/archlinux-x86_64.iso"
    iso_path = Path.home() / "Downloads" / "archlinux-x86_64.iso"

    if iso_path.exists():
        print(f"✅ ISO already exists: {iso_path}")
        return str(iso_path)

    print(f"📥 Downloading from: {iso_url}")
    print(f"📁 Saving to: {iso_path}")

    try:
        response = requests.get(iso_url, stream=True)
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

def list_usb_devices():
    """List available USB devices"""
    print_header("USB DEVICES")

    result = subprocess.run("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E '(disk|part)'",
                          shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("Available storage devices:")
        print(result.stdout)
    else:
        print("❌ Could not list devices")
        return False

    return True

def create_custom_grub_config():
    """Create custom GRUB config with iMac-specific boot options"""
    grub_config = """
menuentry "Arch Linux (Safe Mode - iMac)" {
    set gfxpayload=keep
    linux /arch/boot/x86_64/vmlinuz-linux archisobasedir=arch archisolabel=ARCH_$(date +%Y%m) nomodeset acpi=off noapic pci=nomsi radeon.modeset=0 nouveau.modeset=0 i915.modeset=0 video=vesafb:off
    initrd /arch/boot/x86_64/initramfs-linux.img
}

menuentry "Arch Linux (Text Mode)" {
    set gfxpayload=text
    linux /arch/boot/x86_64/vmlinuz-linux archisobasedir=arch archisolabel=ARCH_$(date +%Y%m) nomodeset text systemd.unit=multi-user.target
    initrd /arch/boot/x86_64/initramfs-linux.img
}

menuentry "Arch Linux (VESA Graphics)" {
    set gfxpayload=1024x768x16
    linux /arch/boot/x86_64/vmlinuz-linux archisobasedir=arch archisolabel=ARCH_$(date +%Y%m) nomodeset vga=792
    initrd /arch/boot/x86_64/initramfs-linux.img
}

menuentry "Arch Linux (Fallback)" {
    set gfxpayload=keep
    linux /arch/boot/x86_64/vmlinuz-linux archisobasedir=arch archisolabel=ARCH_$(date +%Y%m) nomodeset acpi=ht pci=noacpi irqpoll
    initrd /arch/boot/x86_64/initramfs-linux.img
}
"""
    return grub_config

def flash_usb_with_custom_options(iso_path, usb_device):
    """Flash ISO and add custom boot options for iMac"""
    print_header("FLASHING USB WITH iMAC OPTIONS")

    # Verify device exists
    if not os.path.exists(usb_device):
        print(f"❌ Device {usb_device} not found!")
        return False

    # Safety check
    print(f"⚠️  WARNING: This will ERASE ALL DATA on {usb_device}")
    confirm = input("Type 'YES' to continue: ")
    if confirm != "YES":
        print("❌ Aborted by user")
        return False

    # Unmount device if mounted
    print(f"🔄 Unmounting {usb_device}...")
    subprocess.run(f"sudo umount {usb_device}* 2>/dev/null", shell=True)

    # Flash ISO
    dd_cmd = f"sudo dd if={iso_path} of={usb_device} bs=4M status=progress && sync"
    if not run_command(dd_cmd, f"Flashing {iso_path} to {usb_device}"):
        return False

    # Mount the USB to modify boot options
    print("🔧 Adding iMac-specific boot options...")

    # Create mount point
    mount_point = "/tmp/arch_usb_mount"
    subprocess.run(f"sudo mkdir -p {mount_point}", shell=True)

    # Mount USB
    if not run_command(f"sudo mount {usb_device}1 {mount_point}", "Mounting USB for modification"):
        return False

    try:
        # Modify GRUB config for better iMac compatibility
        grub_cfg_path = f"{mount_point}/EFI/BOOT/grub.cfg"
        if os.path.exists(grub_cfg_path):
            # Backup original
            subprocess.run(f"sudo cp {grub_cfg_path} {grub_cfg_path}.backup", shell=True)

            # Read original config
            with open(grub_cfg_path, 'r') as f:
                original_config = f.read()

            # Add iMac-specific entries at the beginning
            custom_config = create_custom_grub_config() + "\n" + original_config

            # Write modified config
            with open(f"/tmp/custom_grub.cfg", 'w') as f:
                f.write(custom_config)

            run_command(f"sudo cp /tmp/custom_grub.cfg {grub_cfg_path}", "Adding custom boot options")
            os.remove("/tmp/custom_grub.cfg")

        # Also modify syslinux config if it exists
        syslinux_cfg_path = f"{mount_point}/arch/boot/syslinux/archiso_sys.cfg"
        if os.path.exists(syslinux_cfg_path):
            subprocess.run(f"sudo cp {syslinux_cfg_path} {syslinux_cfg_path}.backup", shell=True)

            # Add nomodeset to default boot line
            run_command(f"sudo sed -i 's/archisobasedir=arch/archisobasedir=arch nomodeset acpi=off/' {syslinux_cfg_path}",
                       "Modifying syslinux config")

    except Exception as e:
        print(f"⚠️  Warning: Could not modify boot config: {e}")
        print("USB will still work with manual parameter entry")

    finally:
        # Unmount
        run_command(f"sudo umount {mount_point}", "Unmounting USB")
        subprocess.run(f"sudo rmdir {mount_point}", shell=True)

    return True

def flash_usb(iso_path, usb_device):
    """Flash ISO to USB device (legacy method)"""
    print_header("FLASHING USB DRIVE")

    # Verify device exists
    if not os.path.exists(usb_device):
        print(f"❌ Device {usb_device} not found!")
        return False

    # Safety check
    print(f"⚠️  WARNING: This will ERASE ALL DATA on {usb_device}")
    confirm = input("Type 'YES' to continue: ")
    if confirm != "YES":
        print("❌ Aborted by user")
        return False

    # Unmount device if mounted
    print(f"🔄 Unmounting {usb_device}...")
    subprocess.run(f"sudo umount {usb_device}* 2>/dev/null", shell=True)

    # Flash ISO
    dd_cmd = f"sudo dd if={iso_path} of={usb_device} bs=4M status=progress && sync"
    return run_command(dd_cmd, f"Flashing {iso_path} to {usb_device}")

def show_imac_instructions():
    """Display key iMac setup steps"""
    print_header("iMAC BOOT INSTRUCTIONS")

    instructions = [
        "🔌 Plug in USB drive AND ethernet cable to iMac",
        "⌥  Hold Option/Alt key while powering on iMac",
        "💾 Select 'EFI Boot' or USB icon from boot menu",
        "🎯 Try these boot options in order:",
        "   1. Arch Linux (Safe Mode - iMac) ← START HERE",
        "   2. Arch Linux (Text Mode) ← If safe mode fails",
        "   3. Arch Linux (VESA Graphics) ← If text mode fails",
        "   4. Arch Linux (Fallback) ← Last resort"
    ]

    for i, instruction in enumerate(instructions, 1):
        print(f"{i}. {instruction}")

    print(f"\n⚠️  If all fail, try manually adding:")
    print(f"   nomodeset acpi=off noapic radeon.modeset=0")
    print(f"\n📖 Full guide available at: guides/install-arch-sway-on-imac.md")

def main():
    print_header("ARCH LINUX USB PREPARATION")
    print("This script will:")
    print("1. Download Arch Linux ISO")
    print("2. Flash it to your USB drive")
    print("3. Add iMac-specific boot options")
    print("4. Show iMac boot instructions")

    # Download ISO
    iso_path = download_arch_iso()
    if not iso_path:
        print("❌ Failed to download ISO")
        sys.exit(1)

    # List USB devices
    if not list_usb_devices():
        print("❌ Could not list USB devices")
        sys.exit(1)

    # Get USB device from user
    print(f"\n⚠️  WARNING: Choose carefully! Wrong device = data loss!")
    usb_device = input("Enter USB device (e.g., /dev/sdb): ").strip()

    if not usb_device.startswith('/dev/'):
        print("❌ Invalid device path")
        sys.exit(1)

    # Ask user which method to use
    print(f"\n🔧 Choose USB creation method:")
    print(f"1. Enhanced (adds iMac-specific boot options)")
    print(f"2. Standard (basic ISO flash)")
    choice = input("Enter choice (1 or 2): ").strip()

    # Flash USB
    if choice == "1":
        success = flash_usb_with_custom_options(iso_path, usb_device)
    else:
        success = flash_usb(iso_path, usb_device)

    if success:
        print(f"\n✅ USB drive ready: {usb_device}")
        show_imac_instructions()
        print(f"\n🎉 Setup complete! Your USB installer is ready.")
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