# Raspberry Pi Setup - Arch Linux ARM Installation

## Step 1: Flash Arch Linux ARM to SD Card

### Using the Automated Script

We have a Python script that handles everything automatically:

```bash
# Navigate to the PixelParty directory
cd /home/kdresdell/Documents/DEV/PixelParty

# Run the flashing script with sudo
sudo python3 scripts/flash-arch-to-pi.py
```

The script will:
1. Download Arch Linux ARM ARMv7 (recommended version)
2. Show you available SD cards
3. Let you select which one to use
4. Confirm before erasing (type 'YES' to proceed)
5. Automatically partition, format, and install Arch Linux ARM
6. Show progress with colored logging

**Note:** The whole process takes about 10-15 minutes depending on your SD card speed.

---

## Step 2: First Boot Setup

### Connect Your Raspberry Pi
1. Insert the prepared SD card
2. Connect a keyboard and HDMI monitor
3. Connect an ethernet cable (for internet during setup)
4. Power on the Raspberry Pi

### Initial Login
After about 30 seconds, you'll see a login prompt:

```
Default credentials:
Username: alarm
Password: alarm
```

### Essential First Steps

```bash
# 1. Login as alarm user
# Username: alarm
# Password: alarm

# 2. Switch to root user
su
# Password: root

# 3. Initialize the pacman keyring (IMPORTANT - do this first!)
pacman-key --init
pacman-key --populate archlinuxarm

# 4. Update the system
pacman -Syu

# 5. Install essential packages for PixelParty
pacman -S --needed \
    python python-pip \
    git base-devel \
    sudo nano vim \
    hostapd dnsmasq \
    nginx \
    python-flask python-sqlalchemy python-pillow

# 6. Configure sudo for alarm user
echo "alarm ALL=(ALL) ALL" >> /etc/sudoers

# 7. Set your timezone
timedatectl set-timezone America/Montreal

# 8. Change default passwords (IMPORTANT!)
passwd root        # Set a new root password
passwd alarm       # Set a new alarm password
```

---

## Step 3: Install PixelParty

```bash
# 1. Exit root and continue as alarm user
exit

# 2. Create project directory
mkdir -p ~/Documents
cd ~/Documents

# 3. Clone PixelParty repository
git clone https://github.com/YOUR_USERNAME/PixelParty.git
cd PixelParty

# 4. Create Python virtual environment
python -m venv venv
source venv/bin/activate

# 5. Install Python requirements
pip install --upgrade pip
pip install -r requirements.txt

# 6. Create media directories
mkdir -p media/photos media/videos media/music export

# 7. Test that PixelParty runs
python app.py
# You should see: * Running on http://0.0.0.0:5000
# Press Ctrl+C to stop
```

---

## Step 4: Network Information

At this point, find your Pi's IP address:
```bash
ip addr show eth0
# Look for inet line, e.g., inet 192.168.1.100/24
```

You can now access PixelParty from another computer on the same network:
- `http://[YOUR_PI_IP]:5000` - Big screen display
- `http://[YOUR_PI_IP]:5000/mobile` - Mobile interface
- `http://[YOUR_PI_IP]:5000/admin` - Admin panel

---

## Step 5: Optional - Enable SSH Access

If you want to continue setup remotely via SSH:

```bash
# As root (use su)
su

# Install and enable SSH
pacman -S openssh
systemctl enable sshd
systemctl start sshd

# Exit root
exit
```

Now you can SSH from your main computer:
```bash
ssh alarm@[YOUR_PI_IP]
```

---

## Step 6: Next Steps - WiFi Zero-Config Setup

At this point, your Raspberry Pi is ready with:
- ✅ Arch Linux ARM installed
- ✅ PixelParty cloned and tested
- ✅ All dependencies installed
- ✅ Network connectivity

**What's Next:**
We'll run another automated script to configure the Pi as a WiFi access point with zero-configuration for your party guests. This script will:
- Configure the Pi to create its own WiFi network "ValerieParty"
- Set up automatic redirection to PixelParty
- Enable auto-start on boot

But first, make sure PixelParty runs correctly (Step 3, item 7).

---

## Quick Command Reference

```bash
# Check PixelParty is working
cd ~/Documents/PixelParty
source venv/bin/activate
python app.py

# Check system status
systemctl status

# View network interfaces
ip addr

# Check disk space
df -h

# View system logs
journalctl -xe
```

---

## Troubleshooting

**Problem:** Pacman keyring errors
```bash
# Fix: Reinitialize keyring
pacman-key --init
pacman-key --populate archlinuxarm
```

**Problem:** Network not working
```bash
# Check interface status
ip link show
# Restart network
systemctl restart systemd-networkd
```

**Problem:** PixelParty won't start
```bash
# Check Python version (should be 3.9+)
python --version
# Reinstall requirements
pip install --force-reinstall -r requirements.txt
```

---

## Success Checklist

Before proceeding to WiFi setup, verify:
- [ ] Can login as alarm user
- [ ] System is updated (`pacman -Syu` completed)
- [ ] PixelParty repository cloned
- [ ] `python app.py` starts without errors
- [ ] Can access web interface from another computer
- [ ] Changed default passwords

Once all checked, you're ready for the WiFi zero-config setup script!