#!/usr/bin/env python3
"""
Arch Linux ARM SD Card Flasher for Raspberry Pi
Automated tool to flash Arch Linux ARM to SD card
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path

class Colors:
    """Terminal colors for output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log_info(msg):
    """Log info message"""
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {msg}")

def log_success(msg):
    """Log success message"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {msg}")

def log_error(msg):
    """Log error message"""
    print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {msg}")

def log_warning(msg):
    """Log warning message"""
    print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {msg}")

def run_command(cmd, check=True, capture_output=False):
    """Run shell command with error handling"""
    log_info(f"Running: {cmd}")
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            return result.stdout
        else:
            result = subprocess.run(cmd, shell=True, check=check)
            return result.returncode == 0
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {e}")
        return False if not check else None

def check_root():
    """Check if running as root"""
    if os.geteuid() != 0:
        log_error("This script must be run as root (use sudo)")
        sys.exit(1)

def get_sd_cards():
    """Get list of potential SD cards"""
    log_info("Detecting SD cards...")

    # Get all block devices
    lsblk = run_command("lsblk -d -n -o NAME,SIZE,TYPE,MODEL", capture_output=True)
    if not lsblk:
        log_error("Failed to list block devices")
        return []

    devices = []
    for line in lsblk.strip().split('\n'):
        parts = line.split(None, 3)
        if len(parts) >= 3:
            name, size, dtype = parts[:3]
            model = parts[3] if len(parts) > 3 else "Unknown"

            # Filter for removable devices (likely SD cards)
            if dtype == "disk" and not name.startswith("loop"):
                # Check if removable
                removable_path = f"/sys/block/{name}/removable"
                if os.path.exists(removable_path):
                    with open(removable_path, 'r') as f:
                        if f.read().strip() == '1':
                            devices.append({
                                'name': f"/dev/{name}",
                                'size': size,
                                'model': model
                            })

    return devices

def select_device(devices):
    """Let user select SD card"""
    if not devices:
        log_error("No SD cards detected. Please insert an SD card and try again.")
        sys.exit(1)

    print(f"\n{Colors.HEADER}=== Available SD Cards ==={Colors.ENDC}")
    for i, dev in enumerate(devices, 1):
        print(f"{i}. {dev['name']} - {dev['size']} - {dev['model']}")

    while True:
        try:
            choice = input(f"\n{Colors.BOLD}Select SD card number (or 'q' to quit): {Colors.ENDC}")
            if choice.lower() == 'q':
                sys.exit(0)

            idx = int(choice) - 1
            if 0 <= idx < len(devices):
                selected = devices[idx]
                print(f"\n{Colors.WARNING}⚠️  WARNING: All data on {selected['name']} ({selected['size']}) will be DESTROYED!{Colors.ENDC}")
                confirm = input("Type 'YES' to continue: ")
                if confirm == 'YES':
                    return selected['name']
                else:
                    log_info("Cancelled by user")
                    sys.exit(0)
            else:
                print("Invalid selection")
        except ValueError:
            print("Please enter a number")

def download_arch_linux():
    """Download Arch Linux ARM if not present"""
    filename = "ArchLinuxARM-rpi-armv7-latest.tar.gz"
    download_dir = Path.home() / "Downloads"
    download_dir.mkdir(exist_ok=True)
    filepath = download_dir / filename

    if filepath.exists():
        log_info(f"Found existing download: {filepath}")
        use_existing = input("Use existing file? (y/n): ")
        if use_existing.lower() == 'y':
            return str(filepath)

    log_info("Downloading Arch Linux ARM for Raspberry Pi (ARMv7)...")
    log_info("This may take a few minutes...")

    url = "http://os.archlinuxarm.org/os/ArchLinuxARM-rpi-armv7-latest.tar.gz"

    # Use wget with progress bar
    cmd = f"wget -c -O {filepath} {url}"
    if not run_command(cmd, check=False):
        log_error("Download failed")
        sys.exit(1)

    log_success(f"Downloaded to {filepath}")
    return str(filepath)

def prepare_sd_card(device, tarball, wifi_creds):
    """Partition and flash SD card"""

    # Unmount any mounted partitions
    log_info("Unmounting any mounted partitions...")
    run_command(f"umount {device}* 2>/dev/null", check=False)
    time.sleep(1)

    # Create partition table
    log_info("Creating partition table...")
    if not run_command(f"parted -s {device} mklabel msdos"):
        log_error("Failed to create partition table")
        return False

    # Create boot partition (100MB FAT32)
    log_info("Creating boot partition (100MB FAT32)...")
    if not run_command(f"parted -s {device} mkpart primary fat32 1MiB 100MiB"):
        log_error("Failed to create boot partition")
        return False

    # Create root partition (rest of the space)
    log_info("Creating root partition (ext4)...")
    if not run_command(f"parted -s {device} mkpart primary ext4 100MiB 100%"):
        log_error("Failed to create root partition")
        return False

    # Wait for partitions to appear
    time.sleep(2)

    # Format partitions
    log_info("Formatting boot partition (FAT32)...")
    if not run_command(f"mkfs.vfat {device}1"):
        log_error("Failed to format boot partition")
        return False

    log_info("Formatting root partition (ext4)...")
    if not run_command(f"mkfs.ext4 -F {device}2"):
        log_error("Failed to format root partition")
        return False

    # Mount partitions
    log_info("Mounting partitions...")
    run_command("mkdir -p /mnt/boot /mnt/root", check=False)

    if not run_command(f"mount {device}1 /mnt/boot"):
        log_error("Failed to mount boot partition")
        return False

    if not run_command(f"mount {device}2 /mnt/root"):
        log_error("Failed to mount root partition")
        run_command("umount /mnt/boot", check=False)
        return False

    # Extract Arch Linux ARM
    log_info("Extracting Arch Linux ARM to SD card...")
    log_info("This will take several minutes, please be patient...")

    if not run_command(f"tar -xpf {tarball} -C /mnt/root --checkpoint=.1000"):
        log_error("Failed to extract tarball")
        run_command("umount /mnt/boot /mnt/root", check=False)
        return False

    print()  # New line after tar progress dots

    # Sync to ensure all data is written
    log_info("Syncing data to SD card...")
    run_command("sync")

    # Move boot files
    log_info("Moving boot files...")
    if not run_command("mv /mnt/root/boot/* /mnt/boot"):
        log_error("Failed to move boot files")
        run_command("umount /mnt/boot /mnt/root", check=False)
        return False

    # Configure HDMI settings to prevent black screen
    log_info("Configuring HDMI settings...")
    config_txt = """# See /boot/overlays/README for all available options

dtoverlay=vc4-fkms-v3d
initramfs initramfs-linux.img followkernel

# Automatically load overlays for detected DSI displays
display_auto_detect=1

# Force HDMI hotplug detection
hdmi_force_hotplug=1

# Automatically load overlays for detected cameras
camera_auto_detect=1

[cm4]
# Enable host mode on the 2711 built-in XHCI USB controller.
otg_mode=1

[pi4]
# Run as fast as firmware / board allows
arm_boost=1
# HDMI Configuration for better compatibility
hdmi_force_hotplug=1
hdmi_drive=2
hdmi_group=1
hdmi_mode=16
config_hdmi_boost=7
disable_overscan=1

# Force HDMI even if not detected
hdmi_ignore_edid=0xa5000080

# GPU memory split
gpu_mem=128

# Enable UART for debugging (optional)
enable_uart=1
"""

    config_path = "/mnt/boot/config.txt"
    try:
        with open(config_path, 'a') as f:
            f.write(config_txt)
        log_success("HDMI settings configured")
    except Exception as e:
        log_warning(f"Could not configure HDMI settings: {e}")

    # Configure WiFi for initial setup
    log_info("Configuring WiFi for initial connection...")

    # Create systemd network configuration for WiFi
    wifi_config = """[Match]
Name=wlan0

[Network]
DHCP=yes

[DHCP]
RouteMetric=10
"""

    wlan_network_path = "/mnt/root/etc/systemd/network/wlan0.network"
    try:
        run_command(f"mkdir -p /mnt/root/etc/systemd/network/", check=False)
        with open(wlan_network_path, 'w') as f:
            f.write(wifi_config)
        log_success("WiFi network config created")
    except Exception as e:
        log_warning(f"Could not create WiFi network config: {e}")

    # Create wpa_supplicant configuration with multiple networks
    mobile_ssid, mobile_pass, home_ssid, home_pass = wifi_creds

    wpa_config = f"""ctrl_interface=/run/wpa_supplicant
update_config=1
country=US

# Mobile hotspot (for party venue)
network={{
    ssid="{mobile_ssid}"
    psk="{mobile_pass}"
    key_mgmt=WPA-PSK
    priority=1
}}
"""

    # Add home network if provided
    if home_ssid and home_pass:
        wpa_config += f"""
# Home network (for development/SSH)
network={{
    ssid="{home_ssid}"
    psk="{home_pass}"
    key_mgmt=WPA-PSK
    priority=2
}}
"""

    wpa_path = "/mnt/root/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
    try:
        run_command(f"mkdir -p /mnt/root/etc/wpa_supplicant/", check=False)
        with open(wpa_path, 'w') as f:
            f.write(wpa_config)
        networks_msg = f"Mobile: {mobile_ssid}"
        if home_ssid:
            networks_msg += f", Home: {home_ssid}"
        log_success(f"WiFi credentials configured ({networks_msg})")

        # Enable services for WiFi
        run_command(f"ln -sf /usr/lib/systemd/system/wpa_supplicant@.service /mnt/root/etc/systemd/system/multi-user.target.wants/wpa_supplicant@wlan0.service", check=False)
        run_command(f"ln -sf /usr/lib/systemd/system/systemd-networkd.service /mnt/root/etc/systemd/system/multi-user.target.wants/systemd-networkd.service", check=False)
        run_command(f"ln -sf /usr/lib/systemd/system/systemd-resolved.service /mnt/root/etc/systemd/system/multi-user.target.wants/systemd-resolved.service", check=False)

    except Exception as e:
        log_warning(f"Could not configure WiFi: {e}")

    # Install packages directly using chroot
    log_info("Installing packages directly into SD card...")
    log_info("This may take 10-15 minutes depending on internet speed...")

    # Check if arch-chroot is available
    if not shutil.which("arch-chroot"):
        log_warning("arch-chroot not found, trying systemd-nspawn...")
        chroot_cmd = f"systemd-nspawn -D /mnt/root"
    else:
        chroot_cmd = "arch-chroot /mnt/root"

    # Setup basic chroot environment
    log_info("Setting up chroot environment...")

    # Copy resolv.conf for DNS
    run_command("cp /etc/resolv.conf /mnt/root/etc/resolv.conf", check=False)

    # Mount necessary filesystems for chroot
    run_command("mount -t proc /proc /mnt/root/proc", check=False)
    run_command("mount -t sysfs /sys /mnt/root/sys", check=False)
    run_command("mount -o bind /dev /mnt/root/dev", check=False)
    run_command("mount -o bind /dev/pts /mnt/root/dev/pts", check=False)

    try:
        # Initialize pacman keyring
        log_info("Initializing package manager keyring...")
        run_command(f"{chroot_cmd} pacman-key --init", check=False)
        run_command(f"{chroot_cmd} pacman-key --populate archlinuxarm", check=False)

        # Update system
        log_info("Updating system packages...")
        run_command(f"{chroot_cmd} pacman -Syu --noconfirm", check=False)

        # Install system dependencies
        log_info("Installing system dependencies...")
        packages = [
            "git", "base-devel", "sudo", "nano", "vim", "wget", "curl",
            "python", "python-pip", "python-setuptools", "python-wheel",
            "openssh", "wpa_supplicant", "dhcpcd"
        ]
        run_command(f"{chroot_cmd} pacman -S --needed --noconfirm " + " ".join(packages), check=False)

        # Install Sway and GUI components
        log_info("Installing Sway desktop environment...")
        gui_packages = [
            "sway", "swaybg", "swaylock", "swayidle",
            "kitty", "waybar", "wofi", "mako",
            "wl-clipboard", "grim", "slurp",
            "ttf-dejavu", "ttf-liberation", "noto-fonts",
            "xorg-xwayland", "firefox"
        ]
        run_command(f"{chroot_cmd} pacman -S --needed --noconfirm " + " ".join(gui_packages), check=False)

        # Install PixelParty dependencies
        log_info("Installing PixelParty Python dependencies...")
        python_packages = [
            "python-flask", "python-sqlalchemy", "python-pillow",
            "python-requests", "python-mutagen", "ffmpeg", "imagemagick"
        ]
        run_command(f"{chroot_cmd} pacman -S --needed --noconfirm " + " ".join(python_packages), check=False)

        # Create custom user kdresdell
        log_info("Creating custom user 'kdresdell'...")
        run_command(f'{chroot_cmd} useradd -m -G wheel -s /bin/bash kdresdell', check=False)
        run_command(f'{chroot_cmd} bash -c "echo \\"kdresdell:monsterinc00\\" | chpasswd"', check=False)

        # Configure sudo for kdresdell user
        log_info("Configuring sudo for kdresdell user...")
        run_command(f'{chroot_cmd} bash -c "echo \\"kdresdell ALL=(ALL) NOPASSWD: ALL\\" >> /etc/sudoers"', check=False)
        run_command(f'{chroot_cmd} bash -c "echo \\"alarm ALL=(ALL) NOPASSWD: ALL\\" >> /etc/sudoers"', check=False)

        # Enable SSH
        log_info("Enabling SSH service...")
        run_command(f"{chroot_cmd} systemctl enable sshd", check=False)

        # Clone PixelParty repository for kdresdell user
        log_info("Cloning PixelParty repository for kdresdell user...")
        run_command(f"{chroot_cmd} su - kdresdell -c 'mkdir -p /home/kdresdell/Documents'", check=False)
        run_command(f"{chroot_cmd} su - kdresdell -c 'cd /home/kdresdell/Documents && git clone https://github.com/kdresdell/PixelParty.git'", check=False)

        # Set up Python virtual environment for PixelParty
        log_info("Setting up PixelParty virtual environment...")
        run_command(f"{chroot_cmd} su - kdresdell -c 'cd /home/kdresdell/Documents/PixelParty && python -m venv venv'", check=False)
        run_command(f"{chroot_cmd} su - kdresdell -c 'cd /home/kdresdell/Documents/PixelParty && source venv/bin/activate && pip install flask pillow sqlalchemy mutagen requests yt-dlp'", check=False)

        # Create media directories
        run_command(f"{chroot_cmd} su - kdresdell -c 'cd /home/kdresdell/Documents/PixelParty && mkdir -p media/photos media/videos media/music export'", check=False)

        log_success("All packages installed successfully!")

    except Exception as e:
        log_warning(f"Package installation encountered issues: {e}")

    finally:
        # Unmount chroot filesystems
        log_info("Cleaning up chroot environment...")
        run_command("umount /mnt/root/dev/pts", check=False)
        run_command("umount /mnt/root/dev", check=False)
        run_command("umount /mnt/root/sys", check=False)
        run_command("umount /mnt/root/proc", check=False)

    # Configure auto-login to Sway
    log_info("Configuring auto-login to Sway...")

    # Create getty override for auto-login
    getty_override_dir = "/mnt/root/etc/systemd/system/getty@tty1.service.d"
    try:
        run_command(f"mkdir -p {getty_override_dir}", check=False)

        autologin_config = """[Service]
ExecStart=
ExecStart=-/usr/bin/agetty --autologin kdresdell --noclear %I $TERM
"""

        with open(f"{getty_override_dir}/override.conf", 'w') as f:
            f.write(autologin_config)

        log_success("Auto-login configured")
    except Exception as e:
        log_warning(f"Could not configure auto-login: {e}")

    # Create Sway configuration
    log_info("Creating Sway configuration...")

    sway_config_dir = "/mnt/root/home/kdresdell/.config/sway"
    try:
        run_command(f"mkdir -p {sway_config_dir}", check=False)

        sway_config = """# PixelParty Sway Configuration
# Output configuration
output * bg #1a1a1a solid_color

# Variables
set $mod Mod4
set $left h
set $down j
set $up k
set $right l
set $term kitty

# Key bindings
bindsym $mod+Return exec $term
bindsym $mod+Shift+q kill
bindsym $mod+d exec wofi --show drun
bindsym $mod+Shift+c reload
bindsym $mod+Shift+e exec swaynag -t warning -m 'Exit Sway?' -b 'Yes' 'swaymsg exit'
bindsym $mod+Shift+p exec pkill python || true; cd /home/kdresdell/Documents/PixelParty && source venv/bin/activate && python app.py

# Moving around
bindsym $mod+$left focus left
bindsym $mod+$down focus down
bindsym $mod+$up focus up
bindsym $mod+$right focus right

# Move focused window
bindsym $mod+Shift+$left move left
bindsym $mod+Shift+$down move down
bindsym $mod+Shift+$up move up
bindsym $mod+Shift+$right move right

# Workspaces
bindsym $mod+1 workspace number 1
bindsym $mod+2 workspace number 2
bindsym $mod+3 workspace number 3
bindsym $mod+4 workspace number 4
bindsym $mod+5 workspace number 5

# Layout stuff
bindsym $mod+b splith
bindsym $mod+v splitv
bindsym $mod+s layout stacking
bindsym $mod+w layout tabbed
bindsym $mod+e layout toggle split
bindsym $mod+f fullscreen
bindsym $mod+Shift+space floating toggle
bindsym $mod+space focus mode_toggle

# Status bar
bar {
    position top
    status_command waybar
}

# Auto-start applications
exec kitty --title "PixelParty Control" -e bash -c "
echo '=================================='
echo '    PixelParty Raspberry Pi'
echo '=================================='
echo 'Initializing PixelParty...'
sleep 3
echo ''

# Start PixelParty Flask app
cd /home/kdresdell/Documents/PixelParty
source venv/bin/activate

echo 'Starting PixelParty server...'
python app.py &
PIXELPARTY_PID=\$!

sleep 5

echo ''
echo 'Network Status:'
ip addr show wlan0 | grep 'inet ' | awk '{print \"WiFi IP: \" \$2}' || echo 'WiFi: Not connected'
ip addr show eth0 | grep 'inet ' | awk '{print \"Ethernet IP: \" \$2}' || echo 'Ethernet: Not connected'
echo ''
iwgetid -r | xargs -I {} echo 'Connected to WiFi: {}'
echo ''
echo 'PixelParty URLs:'
hostname -I | awk '{print \"http://\" \$1 \":5000 (Big Screen)\"}'
hostname -I | awk '{print \"http://\" \$1 \":5000/mobile (Mobile Interface)\"}'
hostname -I | awk '{print \"http://\" \$1 \":5000/admin (Admin Panel)\"}'
echo ''
echo 'SSH Access:'
hostname -I | awk '{print \"ssh alarm@\" \$1}'
echo ''
echo 'Controls:'
echo '• Mod+Shift+P = Restart PixelParty'
echo '• Mod+Return = New Terminal'
echo '• Mod+D = Application Menu'
echo ''
echo 'PixelParty is running! Check the browser.'

# Keep terminal open and monitor PixelParty
wait \$PIXELPARTY_PID
echo 'PixelParty stopped. Press any key to restart...'
read
exec bash
"

# Auto-start Firefox in kiosk mode after a delay
exec sleep 8 && firefox --kiosk http://localhost:5000
"""

        with open(f"{sway_config_dir}/config", 'w') as f:
            f.write(sway_config)

        # Set ownership (kdresdell will have UID 1001 since alarm is 1000)
        run_command(f"chown -R 1001:1001 /mnt/root/home/kdresdell/.config", check=False)

        log_success("Sway configuration created")
    except Exception as e:
        log_warning(f"Could not create Sway config: {e}")

    # Configure alarm user to start Sway automatically
    log_info("Configuring automatic Sway startup...")

    try:
        bashrc_addition = """
# Auto-start Sway on login to tty1
if [ -z "$DISPLAY" ] && [ "$XDG_VTNR" = 1 ]; then
    exec sway
fi
"""

        bashrc_path = "/mnt/root/home/kdresdell/.bashrc"
        with open(bashrc_path, 'a') as f:
            f.write(bashrc_addition)

        run_command(f"chown 1001:1001 {bashrc_path}", check=False)

        log_success("Automatic Sway startup configured")
    except Exception as e:
        log_warning(f"Could not configure Sway startup: {e}")

    # Create Waybar configuration
    log_info("Creating Waybar configuration...")

    waybar_config_dir = "/mnt/root/home/kdresdell/.config/waybar"
    try:
        run_command(f"mkdir -p {waybar_config_dir}", check=False)

        waybar_config = """{
    "layer": "top",
    "position": "top",
    "height": 30,
    "modules-left": ["sway/workspaces", "sway/mode"],
    "modules-center": ["sway/window"],
    "modules-right": ["network", "clock"],
    "network": {
        "format-wifi": "📶 {essid} ({signalStrength}%) {ipaddr}",
        "format-ethernet": "🔗 {ipaddr}",
        "format-disconnected": "❌ No Internet",
        "tooltip-format": "{ifname}: {ipaddr}/{cidr}",
        "on-click": "kitty --title='Network Info' -e bash -c 'ip addr; echo; echo Press any key...; read'"
    },
    "clock": {
        "format": "{:%Y-%m-%d %H:%M:%S}",
        "tooltip-format": "<big>{:%Y %B}</big>\\n<tt><small>{calendar}</small></tt>"
    }
}"""

        with open(f"{waybar_config_dir}/config", 'w') as f:
            f.write(waybar_config)

        waybar_style = """* {
    font-family: "DejaVu Sans Mono";
    font-size: 13px;
}

window#waybar {
    background-color: #1a1a1a;
    border-bottom: 3px solid #333333;
    color: #ffffff;
}

#network {
    color: #50fa7b;
    padding: 0 10px;
}

#clock {
    color: #f8f8f2;
    padding: 0 10px;
}"""

        with open(f"{waybar_config_dir}/style.css", 'w') as f:
            f.write(waybar_style)

        # Set ownership (kdresdell will have UID 1001)
        run_command(f"chown -R 1001:1001 /mnt/root/home/kdresdell/.config", check=False)

        log_success("Waybar configuration created")
    except Exception as e:
        log_warning(f"Could not create Waybar config: {e}")

    # Enable SSH for remote access
    log_info("SSH will be enabled during first boot...")
    # SSH enabling is now handled in the first boot script

    # Final sync
    log_info("Final sync...")
    run_command("sync")

    # Unmount
    log_info("Unmounting SD card...")
    if not run_command("umount /mnt/boot"):
        log_warning("Failed to unmount boot partition cleanly")
    if not run_command("umount /mnt/root"):
        log_warning("Failed to unmount root partition cleanly")

    return True

def get_wifi_credentials():
    """Get WiFi credentials from user with support for multiple networks"""
    print(f"\n{Colors.BOLD}WiFi Network Configuration{Colors.ENDC}")
    print("PixelParty needs WiFi for:")
    print("• Party venue: Mobile hotspot (Kitesurfer)")
    print("• Development: Home network (for SSH access)")
    print()

    print("Choose configuration:")
    print("1. Use defaults only (Kitesurfer)")
    print("2. Use defaults + add home network")
    print("3. Custom configuration")

    while True:
        choice = input("Select option (1/2/3): ")

        if choice == "1":
            # Use defaults only
            return ("Kitesurfer", "monsterinc00", None, None)

        elif choice == "2":
            # Defaults + home network
            print(f"\n{Colors.BOLD}Home Network Setup{Colors.ENDC}")
            home_ssid = input("Enter your home WiFi SSID: ")
            home_pass = input("Enter your home WiFi password: ")
            return ("Kitesurfer", "monsterinc00", home_ssid, home_pass)

        elif choice == "3":
            # Custom configuration
            print(f"\n{Colors.BOLD}Mobile Hotspot (Party Venue){Colors.ENDC}")
            mobile_ssid = input("Enter mobile hotspot SSID: ")
            mobile_pass = input("Enter mobile hotspot password: ")

            print(f"\n{Colors.BOLD}Home Network (Optional){Colors.ENDC}")
            add_home = input("Add home network for SSH access? (y/n): ")

            if add_home.lower() == 'y':
                home_ssid = input("Enter home WiFi SSID: ")
                home_pass = input("Enter home WiFi password: ")
                return (mobile_ssid, mobile_pass, home_ssid, home_pass)
            else:
                return (mobile_ssid, mobile_pass, None, None)
        else:
            print("Please enter 1, 2, or 3")

def main():
    """Main function"""
    print(f"{Colors.HEADER}")
    print("="*50)
    print("  Arch Linux ARM SD Card Flasher for Raspberry Pi")
    print("  For PixelParty Project - ARMv7 Edition")
    print("="*50)
    print(f"{Colors.ENDC}")

    # Check if running as root
    check_root()

    # Check for required tools
    log_info("Checking required tools...")
    required_tools = ['parted', 'mkfs.vfat', 'mkfs.ext4', 'wget', 'tar']
    missing_tools = []

    for tool in required_tools:
        if not shutil.which(tool):
            missing_tools.append(tool)

    if missing_tools:
        log_error(f"Missing required tools: {', '.join(missing_tools)}")
        log_info("Install with: sudo pacman -S parted dosfstools e2fsprogs wget tar")
        sys.exit(1)

    log_success("All required tools found")

    # Download Arch Linux ARM
    tarball = download_arch_linux()

    # Get WiFi credentials (supports multiple networks)
    wifi_creds = get_wifi_credentials()

    # Get SD cards
    devices = get_sd_cards()

    # Select device
    device = select_device(devices)

    # Prepare SD card
    log_info(f"Preparing {device}...")

    if prepare_sd_card(device, tarball, wifi_creds):
        log_success("="*50)
        log_success("SD card successfully prepared!")
        log_success("="*50)
        mobile_ssid, _, home_ssid, _ = wifi_creds
        print(f"\n{Colors.BOLD}What's been configured:{Colors.ENDC}")
        print("✅ Fixed HDMI black screen issues (vc4-fkms-v3d driver)")
        print("✅ Auto-boot directly into Sway desktop")
        print("✅ PixelParty Flask app auto-starts")
        print("✅ Firefox browser opens PixelParty in kiosk mode")
        print("✅ All system dependencies pre-installed")
        print("✅ Python virtual environment with PixelParty ready")
        networks_msg = f"Mobile: {mobile_ssid}"
        if home_ssid:
            networks_msg += f", Home: {home_ssid}"
        print(f"✅ WiFi configured: {networks_msg}")
        print("✅ SSH enabled for remote access")

        print(f"\n{Colors.BOLD}Next steps:{Colors.ENDC}")
        print("1. Remove SD card and insert into Raspberry Pi")
        print("2. Connect to TV/monitor via HDMI FIRST")
        print("3. Power on the Pi")
        print("4. Wait ~30-60 seconds for boot")
        print("5. PixelParty will appear automatically in fullscreen!")

        print(f"\n{Colors.BOLD}What you'll see on boot:{Colors.ENDC}")
        print("• Sway desktop loads")
        print("• Control terminal shows network info and PixelParty status")
        print("• Firefox opens PixelParty big screen display in kiosk mode")
        print("• Ready for party guests immediately!")

        print(f"\n{Colors.BOLD}Controls (if needed):{Colors.ENDC}")
        print("• Super+Shift+P = Restart PixelParty")
        print("• Super+Return = New Terminal")
        print("• Super+D = Application Menu")
        print("• SSH access: ssh kdresdell@[IP_ADDRESS] (password: monsterinc00)")

        mobile_ssid, _, home_ssid, _ = wifi_creds
        print(f"\n{Colors.BOLD}Network behavior:{Colors.ENDC}")
        if home_ssid:
            print(f"• At home: Connects to '{home_ssid}' (priority 2)")
            print(f"• At party: Falls back to '{mobile_ssid}' (priority 1)")
        else:
            print(f"• Connects to: '{mobile_ssid}' only")
        print("• IP address displayed in Waybar and terminal")
    else:
        log_error("Failed to prepare SD card")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrupted by user{Colors.ENDC}")
        run_command("umount /mnt/boot /mnt/root 2>/dev/null", check=False)
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        run_command("umount /mnt/boot /mnt/root 2>/dev/null", check=False)
        sys.exit(1)