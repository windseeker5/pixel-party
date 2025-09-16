#!/usr/bin/env python3
"""
Create Custom Arch Linux ISO for iMac
Pre-configures boot parameters to avoid manual editing
"""

import os
import sys
import subprocess
import requests
import tempfile
import shutil
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

def check_dependencies():
    """Check if required tools are installed"""
    print_header("CHECKING DEPENDENCIES")

    # Check if archiso package is installed
    result = subprocess.run("pacman -Q archiso", shell=True, capture_output=True)
    if result.returncode != 0:
        print(f"❌ Missing package: archiso")
        print(f"📦 Install with: sudo pacman -S archiso")
        return False

    # Check if mkarchiso command exists
    result = subprocess.run("which mkarchiso", shell=True, capture_output=True)
    if result.returncode != 0:
        print(f"❌ mkarchiso command not found")
        print(f"📦 Install with: sudo pacman -S archiso")
        return False

    # Check if archiso configs exist
    config_path = "/usr/share/archiso/configs/releng"
    if not os.path.exists(config_path):
        print(f"❌ Archiso configs not found at {config_path}")
        print(f"📦 Install with: sudo pacman -S archiso")
        return False

    print("✅ All dependencies found")
    print(f"   • archiso package: installed")
    print(f"   • mkarchiso command: available")
    print(f"   • archiso configs: available")
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

def create_custom_archiso():
    """Create custom archiso with iMac boot parameters"""
    print_header("CREATING CUSTOM ARCHISO")

    # Create working directory
    work_dir = Path.home() / "imac_arch_build"
    work_dir.mkdir(exist_ok=True)

    # Copy archiso profile
    profile_dir = work_dir / "myiso"
    if profile_dir.exists():
        shutil.rmtree(profile_dir)

    if not run_command(f"cp -r /usr/share/archiso/configs/releng/ {profile_dir}",
                      "Copying archiso profile"):
        return None

    # Modify UEFI boot config
    uefi_config = profile_dir / "efiboot" / "loader" / "entries" / "01-archiso-x86_64-linux.conf"
    if uefi_config.exists():
        print("🔧 Modifying UEFI boot config...")

        # Read original config
        with open(uefi_config, 'r') as f:
            content = f.read()

        # Add ATI Radeon HD 2400 specific boot parameters
        imac_params = "radeon.modeset=0 nomodeset acpi=off noapic pci=nomsi radeon.agpmode=-1 video=vesafb:off"

        # Replace options line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('options'):
                lines[i] = f"{line} {imac_params}"
                break

        # Write modified config
        with open(uefi_config, 'w') as f:
            f.write('\n'.join(lines))

        print("✅ UEFI config modified")

    # Modify BIOS boot config
    bios_config = profile_dir / "syslinux" / "archiso_sys-linux.cfg"
    if bios_config.exists():
        print("🔧 Modifying BIOS boot config...")

        with open(bios_config, 'r') as f:
            content = f.read()

        # Add ATI Radeon HD 2400 specific boot parameters to APPEND line
        imac_params = "radeon.modeset=0 nomodeset acpi=off noapic pci=nomsi radeon.agpmode=-1 video=vesafb:off"

        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('APPEND') and 'archisobasedir=arch' in line:
                lines[i] = f"{line} {imac_params}"
                break

        with open(bios_config, 'w') as f:
            f.write('\n'.join(lines))

        print("✅ BIOS config modified")

    return profile_dir

def build_iso(profile_dir):
    """Build the custom ISO"""
    print_header("BUILDING CUSTOM ISO")

    output_dir = Path.home() / "Downloads"
    work_temp = "/tmp/archiso-imac-build"

    # Clean previous build
    if os.path.exists(work_temp):
        run_command(f"sudo rm -rf {work_temp}", "Cleaning previous build")

    # Build ISO
    build_cmd = f"sudo mkarchiso -v -w {work_temp} -o {output_dir} {profile_dir}"

    print("🏗️  Building ISO (this will take 10-15 minutes)...")
    print("☕ Grab some coffee while this runs...")

    if run_command(build_cmd, "Building custom Arch ISO"):
        # Find the built ISO
        iso_files = list(output_dir.glob("archlinux-*-x86_64.iso"))
        if iso_files:
            latest_iso = max(iso_files, key=os.path.getctime)
            print(f"✅ Custom ISO created: {latest_iso}")
            return str(latest_iso)

    return None

def flash_custom_iso(iso_path):
    """Flash the custom ISO to USB"""
    print_header("FLASH CUSTOM ISO TO USB")

    # List USB devices
    result = subprocess.run("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E '(disk|part)'",
                          shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("Available storage devices:")
        print(result.stdout)

    # Get USB device
    print(f"\n⚠️  WARNING: Choose carefully! Wrong device = data loss!")
    usb_device = input("Enter USB device (e.g., /dev/sdb): ").strip()

    if not usb_device.startswith('/dev/'):
        print("❌ Invalid device path")
        return False

    if not os.path.exists(usb_device):
        print(f"❌ Device {usb_device} not found!")
        return False

    # Safety check
    print(f"⚠️  WARNING: This will ERASE ALL DATA on {usb_device}")
    confirm = input("Type 'YES' to continue: ")
    if confirm != "YES":
        print("❌ Aborted by user")
        return False

    # Unmount and flash
    subprocess.run(f"sudo umount {usb_device}* 2>/dev/null", shell=True)

    dd_cmd = f"sudo dd if={iso_path} of={usb_device} bs=4M status=progress oflag=sync"
    return run_command(dd_cmd, f"Flashing custom ISO to {usb_device}")

def show_success_instructions():
    """Show success instructions"""
    print_header("SUCCESS! iMAC BOOT INSTRUCTIONS")

    instructions = [
        "🔌 Plug USB into iMac + ethernet cable",
        "⌥  Hold Option/Alt while powering on",
        "💾 Select USB/EFI Boot",
        "🎯 Boot should work automatically - NO MORE EDITING!"
    ]

    for i, instruction in enumerate(instructions, 1):
        print(f"{i}. {instruction}")

    print(f"\n✨ What's different:")
    print(f"   • Custom ISO optimized for ATI Radeon HD 2400")
    print(f"   • Parameters: radeon.modeset=0 nomodeset acpi=off")
    print(f"   • Includes radeon.agpmode=-1 for old ATI cards")
    print(f"   • No need to press 'e' or edit anything")
    print(f"   • Should boot directly past black screen")

def main():
    print_header("ARCH LINUX iMAC CUSTOM ISO CREATOR")
    print("🍎 Optimized for ATI Radeon HD 2400 (128MB VRAM)")
    print("🚫 NO MORE PRESSING 'E' OR MANUAL EDITING!")
    print("⚡ Using specific parameters for your old ATI GPU")

    # Check dependencies
    if not check_dependencies():
        print("\n💡 Install archiso first: sudo pacman -S archiso")
        sys.exit(1)

    # Create custom archiso
    profile_dir = create_custom_archiso()
    if not profile_dir:
        print("❌ Failed to create custom archiso")
        sys.exit(1)

    # Build ISO
    iso_path = build_iso(profile_dir)
    if not iso_path:
        print("❌ Failed to build custom ISO")
        sys.exit(1)

    # Flash to USB
    if flash_custom_iso(iso_path):
        show_success_instructions()
        print(f"\n🎉 Custom iMac Arch ISO ready! No more editing required!")
    else:
        print("❌ Failed to flash USB")
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