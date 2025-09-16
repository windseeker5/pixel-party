#!/usr/bin/env python3
"""
Flash Raspberry Pi OS to SD Card
Simple, reliable setup for PixelParty
"""

import os
import sys
import subprocess
import time
import shutil
import urllib.request
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

def log_warning(msg):
    print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {msg}")

def run_command(cmd, check=True, capture_output=False):
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
        return False

def check_root():
    if os.geteuid() != 0:
        log_error("This script must be run as root (use sudo)")
        sys.exit(1)

def get_sd_cards():
    log_info("Detecting SD cards...")

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

            if dtype == "disk" and not name.startswith("loop"):
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
    if not devices:
        log_error("No SD cards detected. Please insert an SD card and try again.")
        sys.exit(1)

    print(f"\n{Colors.GREEN}=== Available SD Cards ==={Colors.ENDC}")
    for i, dev in enumerate(devices, 1):
        print(f"{i}. {dev['name']} - {dev['size']} - {dev['model']}")

    while True:
        try:
            choice = input(f"\n{Colors.WARNING}Select SD card number (or 'q' to quit): {Colors.ENDC}")
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

def download_raspios():
    """Download Raspberry Pi OS Lite"""
    downloads_dir = Path.home() / "Downloads"
    downloads_dir.mkdir(exist_ok=True)

    # Use Raspberry Pi OS Lite (smaller, faster)
    filename = "2024-07-04-raspios-bookworm-arm64-lite.img.xz"
    url = f"https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2024-07-04/{filename}"
    filepath = downloads_dir / filename

    if filepath.exists():
        log_info(f"Found existing download: {filepath}")
        use_existing = input("Use existing file? (y/n): ")
        if use_existing.lower() == 'y':
            return str(filepath)

    log_info("Downloading Raspberry Pi OS Lite (ARM64)...")
    log_info("This may take 10-15 minutes depending on your internet speed...")

    try:
        # Download with progress
        def progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, (downloaded * 100) // total_size)
                print(f"\rProgress: {percent}%", end="", flush=True)

        urllib.request.urlretrieve(url, filepath, progress_hook)
        print()  # New line after progress
        log_success(f"Downloaded to {filepath}")
        return str(filepath)

    except Exception as e:
        log_error(f"Download failed: {e}")
        log_info("You can manually download from: https://www.raspberrypi.org/software/operating-systems/")
        sys.exit(1)

def flash_image(device, image_path):
    """Flash the image to SD card"""

    log_info("Unmounting any mounted partitions...")
    run_command(f"umount {device}* 2>/dev/null", check=False)
    time.sleep(1)

    # Extract if compressed
    if image_path.endswith('.xz'):
        log_info("Extracting compressed image...")
        extracted_path = image_path[:-3]  # Remove .xz extension
        if not os.path.exists(extracted_path):
            run_command(f"xz -d -k '{image_path}'")
        image_path = extracted_path

    log_info("Flashing Raspberry Pi OS to SD card...")
    log_info("This will take 5-10 minutes...")

    # Use dd to flash the image
    if not run_command(f"dd if='{image_path}' of={device} bs=4M status=progress conv=fsync"):
        log_error("Failed to flash image")
        return False

    log_info("Syncing data...")
    run_command("sync")
    time.sleep(2)

    return True

def configure_pi(device):
    """Configure the Pi for immediate use"""

    log_info("Configuring Raspberry Pi...")

    # Mount the boot partition
    run_command("mkdir -p /mnt/boot")
    if not run_command(f"mount {device}1 /mnt/boot"):
        log_warning("Could not mount boot partition for configuration")
        return

    try:
        # Enable SSH
        log_info("Enabling SSH...")
        with open("/mnt/boot/ssh", 'w') as f:
            f.write("")

        # Configure WiFi
        log_info("Configuring WiFi...")
        wifi_config = """country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="Kitesurfer"
    psk="monsterinc00"
}
"""
        with open("/mnt/boot/wpa_supplicant.conf", 'w') as f:
            f.write(wifi_config)

        # Create user configuration (new Pi OS method)
        log_info("Creating user configuration...")
        # Hash for password "monsterinc00"
        password_hash = run_command("echo 'monsterinc00' | openssl passwd -6 -stdin", capture_output=True).strip()

        user_config = f"""kdresdell:{password_hash}
"""
        with open("/mnt/boot/userconf.txt", 'w') as f:
            f.write(user_config)

        # Create config for first boot setup
        log_info("Creating first-boot setup...")
        setup_script = """#!/bin/bash
# First boot setup for PixelParty

# Update system
apt update
apt upgrade -y

# Install required packages
apt install -y python3-pip python3-venv git chromium-browser unclutter

# Clone PixelParty
cd /home/kdresdell
sudo -u kdresdell git clone https://github.com/kdresdell/PixelParty.git

# Set up Python environment
cd /home/kdresdell/PixelParty
sudo -u kdresdell python3 -m venv venv
sudo -u kdresdell bash -c 'source venv/bin/activate && pip install -r requirements.txt'

# Create media directories
sudo -u kdresdell mkdir -p media/photos media/videos media/music export

# Create startup script
cat > /home/kdresdell/start-pixelparty.sh << 'EOF'
#!/bin/bash
cd /home/kdresdell/PixelParty
source venv/bin/activate
python app.py &
sleep 5
chromium-browser --start-fullscreen --kiosk http://localhost:5000
EOF

chmod +x /home/kdresdell/start-pixelparty.sh
chown kdresdell:kdresdell /home/kdresdell/start-pixelparty.sh

# Remove this setup script
rm -f /etc/rc.local
"""

        with open("/mnt/boot/setup.sh", 'w') as f:
            f.write(setup_script)

        # Create rc.local to run setup on first boot
        rc_local = """#!/bin/sh -e
# Run first boot setup
if [ -f /boot/setup.sh ]; then
    bash /boot/setup.sh
    rm -f /boot/setup.sh
fi
exit 0
"""
        with open("/mnt/boot/rc.local", 'w') as f:
            f.write(rc_local)

    except Exception as e:
        log_warning(f"Configuration partially failed: {e}")

    finally:
        run_command("umount /mnt/boot", check=False)

def main():
    print(f"{Colors.GREEN}")
    print("=" * 50)
    print("  Raspberry Pi OS Flasher for PixelParty")
    print("  Simple, Reliable Setup")
    print("=" * 50)
    print(f"{Colors.ENDC}")

    check_root()

    # Check for required tools
    required_tools = ['dd', 'xz', 'openssl']
    missing_tools = []
    for tool in required_tools:
        if not shutil.which(tool):
            missing_tools.append(tool)

    if missing_tools:
        log_error(f"Missing required tools: {', '.join(missing_tools)}")
        log_info("Install with: sudo pacman -S coreutils xz openssl")
        sys.exit(1)

    # Get devices
    devices = get_sd_cards()
    device = select_device(devices)

    # Download Raspberry Pi OS
    image_path = download_raspios()

    # Flash image
    if flash_image(device, image_path):
        # Configure Pi
        configure_pi(device)

        log_success("=" * 50)
        log_success("Raspberry Pi OS flashed successfully!")
        log_success("=" * 50)

        print(f"\n{Colors.GREEN}Configuration:{Colors.ENDC}")
        print("✅ SSH enabled")
        print("✅ WiFi configured for 'Kitesurfer' network")
        print("✅ User: kdresdell / monsterinc00")
        print("✅ PixelParty will be set up on first boot")

        print(f"\n{Colors.GREEN}Next steps:{Colors.ENDC}")
        print("1. Insert SD card into Raspberry Pi")
        print("2. Connect to monitor via HDMI")
        print("3. Power on and wait 5-10 minutes for first boot setup")
        print("4. Login: kdresdell / monsterinc00")
        print("5. Run: ./start-pixelparty.sh")

        print(f"\n{Colors.GREEN}URLs after setup:{Colors.ENDC}")
        print("• Big Screen: http://localhost:5000")
        print("• Mobile: http://[PI_IP]:5000/mobile")
        print("• Admin: http://[PI_IP]:5000/admin")

    else:
        log_error("Failed to flash Raspberry Pi OS")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrupted by user{Colors.ENDC}")
        run_command("umount /mnt/boot 2>/dev/null", check=False)
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        run_command("umount /mnt/boot 2>/dev/null", check=False)
        sys.exit(1)