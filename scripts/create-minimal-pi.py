#!/usr/bin/env python3
"""
Create a minimal, clean Raspberry Pi bootable image
Just basic Arch Linux ARM with working display and SSH
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def log_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {msg}")

def log_success(msg):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {msg}")

def log_error(msg):
    print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {msg}")

def run_command(cmd, check=True):
    log_info(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {e}")
        return False

def main():
    print(f"{Colors.GREEN}🔧 Creating Minimal Raspberry Pi Image{Colors.ENDC}")
    print("=" * 50)

    # Check root
    if os.geteuid() != 0:
        log_error("Run with: sudo python3 create-minimal-pi.py")
        sys.exit(1)

    # Get SD card
    print("\nAvailable devices:")
    run_command("lsblk -d -o NAME,SIZE,MODEL | grep -E 'sd[a-z]'")

    device = input("\nEnter SD card device (e.g., /dev/sdc): ").strip()
    if not device.startswith('/dev/'):
        device = f"/dev/{device}"

    print(f"⚠️  ALL DATA ON {device} WILL BE DESTROYED!")
    confirm = input("Type 'YES' to continue: ")
    if confirm != 'YES':
        print("Cancelled")
        sys.exit(0)

    # Download if needed
    tarball = Path.home() / "Downloads" / "ArchLinuxARM-rpi-armv7-latest.tar.gz"
    if not tarball.exists():
        log_info("Downloading Arch Linux ARM...")
        run_command(f"wget -O {tarball} http://os.archlinuxarm.org/os/ArchLinuxARM-rpi-armv7-latest.tar.gz")

    # Partition and format
    log_info("Creating partitions...")
    run_command(f"umount {device}* 2>/dev/null", check=False)
    run_command(f"parted -s {device} mklabel msdos")
    run_command(f"parted -s {device} mkpart primary fat32 1MiB 100MiB")
    run_command(f"parted -s {device} mkpart primary ext4 100MiB 100%")
    time.sleep(2)

    log_info("Formatting partitions...")
    run_command(f"mkfs.vfat {device}1")
    run_command(f"mkfs.ext4 -F {device}2")

    # Mount and extract
    log_info("Mounting and extracting...")
    run_command("mkdir -p /mnt/boot /mnt/root")
    run_command(f"mount {device}1 /mnt/boot")
    run_command(f"mount {device}2 /mnt/root")

    log_info("Extracting Arch Linux ARM (this takes time)...")
    run_command(f"tar -xpf {tarball} -C /mnt/root")
    run_command("mv /mnt/root/boot/* /mnt/boot")

    # Create minimal config
    log_info("Creating minimal config...")

    config_txt = """# Minimal HDMI Configuration
dtoverlay=vc4-fkms-v3d
initramfs initramfs-linux.img followkernel
hdmi_force_hotplug=1
hdmi_group=1
hdmi_mode=16
gpu_mem=64
enable_uart=1
camera_auto_detect=1
display_auto_detect=1

[pi4]
arm_boost=1
"""

    with open("/mnt/boot/config.txt", 'w') as f:
        f.write(config_txt)

    # Enable SSH
    with open("/mnt/boot/ssh", 'w') as f:
        f.write("")

    # WiFi config
    wpa_config = """ctrl_interface=/run/wpa_supplicant
update_config=1
country=US

network={
    ssid="Kitesurfer"
    psk="monsterinc00"
    key_mgmt=WPA-PSK
}
"""

    os.makedirs("/mnt/root/etc/wpa_supplicant", exist_ok=True)
    with open("/mnt/root/etc/wpa_supplicant/wpa_supplicant-wlan0.conf", 'w') as f:
        f.write(wpa_config)

    # Network config
    network_config = """[Match]
Name=wlan0

[Network]
DHCP=yes

[DHCP]
RouteMetric=10
"""

    os.makedirs("/mnt/root/etc/systemd/network", exist_ok=True)
    with open("/mnt/root/etc/systemd/network/wlan0.network", 'w') as f:
        f.write(network_config)

    # Enable services
    run_command("ln -sf /usr/lib/systemd/system/sshd.service /mnt/root/etc/systemd/system/multi-user.target.wants/sshd.service", check=False)
    run_command("ln -sf /usr/lib/systemd/system/wpa_supplicant@.service /mnt/root/etc/systemd/system/multi-user.target.wants/wpa_supplicant@wlan0.service", check=False)
    run_command("ln -sf /usr/lib/systemd/system/systemd-networkd.service /mnt/root/etc/systemd/system/multi-user.target.wants/systemd-networkd.service", check=False)

    # Cleanup and unmount
    run_command("sync")
    run_command("umount /mnt/boot /mnt/root")

    log_success("✅ MINIMAL RASPBERRY PI IMAGE CREATED!")
    log_success("Login: alarm / alarm")
    log_success("SSH will be enabled")
    log_success("WiFi: Kitesurfer network")
    print("\nReady to boot! Insert SD card and power on.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled")
        run_command("umount /mnt/boot /mnt/root 2>/dev/null", check=False)
        sys.exit(1)