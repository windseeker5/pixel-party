#!/usr/bin/env python3
"""
Raspberry Pi SD Card Fix Script
Fixes black screen and WiFi connectivity issues by editing config files directly on SD card.
"""

import os
import sys
import subprocess
import psutil
from pathlib import Path

def get_color(color_name):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'end': '\033[0m'
    }
    return colors.get(color_name, '')

def print_colored(text, color):
    print(f"{get_color(color)}{text}{get_color('end')}")

def find_sd_card_partitions():
    """Find SD card partitions - typically boot and root partitions"""
    partitions = psutil.disk_partitions()
    sd_partitions = []

    print_colored("\n🔍 Looking for SD card partitions...", 'blue')

    for partition in partitions:
        try:
            # Look for removable media or specific mount points
            if (partition.mountpoint.startswith('/media') or
                partition.mountpoint.startswith('/mnt') or
                'boot' in partition.mountpoint.lower() or
                'BOOT' in partition.mountpoint):

                usage = psutil.disk_usage(partition.mountpoint)
                size_gb = usage.total / (1024**3)

                print(f"  📁 {partition.device} -> {partition.mountpoint}")
                print(f"     Size: {size_gb:.1f}GB, FS: {partition.fstype}")

                sd_partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'size_gb': size_gb
                })
        except (PermissionError, FileNotFoundError):
            continue

    return sd_partitions

def fix_hdmi_config(boot_path):
    """Fix HDMI black screen by modifying config.txt"""
    config_files = [
        os.path.join(boot_path, 'config.txt'),
        os.path.join(boot_path, 'firmware', 'config.txt')
    ]

    config_file = None
    for cf in config_files:
        if os.path.exists(cf):
            config_file = cf
            break

    if not config_file:
        print_colored(f"❌ config.txt not found in {boot_path}", 'red')
        return False

    print_colored(f"📝 Fixing HDMI config in {config_file}", 'yellow')

    # Read existing config
    try:
        with open(config_file, 'r') as f:
            content = f.read()
    except Exception as e:
        print_colored(f"❌ Error reading {config_file}: {e}", 'red')
        return False

    # HDMI fixes to add
    hdmi_fixes = """
# HDMI Black Screen Fixes
hdmi_force_hotplug=1
config_hdmi_boost=7
hdmi_safe=1

# Use compatible video driver
dtoverlay=vc4-fkms-v3d
"""

    # Check if fixes already exist
    if 'hdmi_force_hotplug=1' in content:
        print_colored("✅ HDMI fixes already present", 'green')
    else:
        # Add fixes at the end
        content += hdmi_fixes

        try:
            with open(config_file, 'w') as f:
                f.write(content)
            print_colored("✅ HDMI fixes added to config.txt", 'green')
        except Exception as e:
            print_colored(f"❌ Error writing {config_file}: {e}", 'red')
            return False

    return True

def enable_ssh(boot_path):
    """Enable SSH by creating ssh file"""
    ssh_file = os.path.join(boot_path, 'ssh')

    try:
        with open(ssh_file, 'w') as f:
            f.write('')  # Empty file
        print_colored("✅ SSH enabled", 'green')
        return True
    except Exception as e:
        print_colored(f"❌ Error creating SSH file: {e}", 'red')
        return False

def configure_wifi(boot_path, ssid, password):
    """Configure WiFi for the hotspot"""
    wpa_file = os.path.join(boot_path, 'wpa_supplicant.conf')

    wpa_config = f"""country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""

    try:
        with open(wpa_file, 'w') as f:
            f.write(wpa_config)
        print_colored("✅ WiFi configuration created", 'green')
        return True
    except Exception as e:
        print_colored(f"❌ Error creating WiFi config: {e}", 'red')
        return False

def main():
    print_colored("🔧 Raspberry Pi SD Card Fix Tool", 'cyan')
    print_colored("=" * 50, 'cyan')

    # Check if running as root for some operations
    if os.geteuid() == 0:
        print_colored("⚠️  Running as root - be careful!", 'yellow')

    # Find SD card partitions
    partitions = find_sd_card_partitions()

    if not partitions:
        print_colored("❌ No SD card partitions found!", 'red')
        print_colored("Make sure your SD card is inserted and mounted.", 'red')
        sys.exit(1)

    # Show partitions and let user choose
    print_colored("\n📋 Available partitions:", 'blue')
    for i, part in enumerate(partitions):
        print(f"  {i+1}. {part['device']} -> {part['mountpoint']}")
        print(f"     Size: {part['size_gb']:.1f}GB, FS: {part['fstype']}")

    # Auto-detect boot partition (usually FAT32 and smaller)
    boot_partition = None
    for part in partitions:
        if part['fstype'].lower() in ['fat32', 'fat', 'vfat', 'msdos'] and part['size_gb'] < 1:
            boot_partition = part
            break

    if boot_partition:
        print_colored(f"\n🎯 Auto-detected boot partition: {boot_partition['mountpoint']}", 'green')
        use_auto = input("Use this partition? (y/n): ").lower().strip()
        if use_auto != 'y':
            boot_partition = None

    if not boot_partition:
        try:
            choice = int(input("\nSelect boot partition number: ")) - 1
            boot_partition = partitions[choice]
        except (ValueError, IndexError):
            print_colored("❌ Invalid selection!", 'red')
            sys.exit(1)

    boot_path = boot_partition['mountpoint']
    print_colored(f"\n🚀 Working with boot partition: {boot_path}", 'cyan')

    # Get WiFi credentials
    print_colored("\n📶 WiFi Configuration", 'blue')
    ssid = input("Enter your hotspot name (SSID): ").strip()
    password = input("Enter your hotspot password: ").strip()

    if not ssid:
        print_colored("❌ SSID cannot be empty!", 'red')
        sys.exit(1)

    # Apply fixes
    success_count = 0

    print_colored(f"\n🔧 Applying fixes to {boot_path}...", 'cyan')

    if fix_hdmi_config(boot_path):
        success_count += 1

    if enable_ssh(boot_path):
        success_count += 1

    if configure_wifi(boot_path, ssid, password):
        success_count += 1

    print_colored(f"\n✅ Applied {success_count}/3 fixes successfully!", 'green')

    if success_count == 3:
        print_colored("\n🎉 SD card fixes complete! Next steps:", 'green')
        print("1. Safely eject the SD card")
        print("2. Insert into Raspberry Pi")
        print("3. Connect HDMI cable BEFORE powering on")
        print("4. Power on and wait 2-3 minutes")
        print("5. Check your hotspot for Pi connection")
        print(f"6. Try SSH: ssh alarm@[PI_IP] (password: alarm)")
    else:
        print_colored("\n⚠️  Some fixes failed. Check the errors above.", 'yellow')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n🛑 Operation cancelled by user", 'yellow')
        sys.exit(0)