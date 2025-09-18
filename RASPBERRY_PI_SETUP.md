# Raspberry Pi Setup Guide for PixelParty

## Prerequisites
- Raspberry Pi 4 with Raspberry Pi OS Lite
- Network connection
- SSH access to the Pi

## Step 1: System Update
```bash
sudo apt update && sudo apt upgrade -y
```

## Step 2: Install Sway and Chromium
```bash
# Install Sway compositor and Chromium
sudo apt install -y sway chromium-browser

# Install audio support
sudo apt install -y pulseaudio alsa-utils
```

## Step 3: Install Python Environment
```bash
# Install Python dependencies
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential

# Install media processing libraries
sudo apt install -y libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libopenjp2-7-dev libtiff5-dev
```

## Step 4: Setup PixelParty
```bash
# Clone and setup (adjust repo URL)
git clone <your-repo-url> PixelParty
cd PixelParty

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create media directories
mkdir -p media/photos media/videos media/music
```

## Step 5: Configure Sway for Kiosk Mode
```bash
# Create sway config directory
mkdir -p ~/.config/sway

# Create sway config
nano ~/.config/sway/config
```

Add this minimal config:
```
# Disable title bars and borders
default_border none
default_floating_border none

# Set background color
output * bg #000000 solid_color

# Key bindings (minimal for debugging)
bindsym $mod+Return exec chromium-browser --enable-features=UseOzonePlatform --ozone-platform=wayland --kiosk http://localhost:5000
bindsym $mod+Shift+q exit

# Set mod key to Super (Windows key)
set $mod Mod4
```

## Manual Startup Process

### 1. Start PixelParty Flask App
```bash
cd ~/PixelParty
source venv/bin/activate
python app.py
```

### 2. Start Sway (in another terminal/SSH session)
```bash
sway
```

### 3. Launch Chromium in Kiosk Mode
Once Sway is running, press `Super+Enter` or manually run:
```bash
chromium-browser --enable-features=UseOzonePlatform --ozone-platform=wayland --kiosk --disable-infobars --no-first-run http://localhost:5000
```

## Alternative: One-Line Startup Script
Create a simple script to start everything:

```bash
# Create startup script
nano ~/start_pixelparty.sh
```

Add:
```bash
#!/bin/bash
cd ~/PixelParty
source venv/bin/activate
python app.py &
sleep 3
sway &
sleep 2
chromium-browser --enable-features=UseOzonePlatform --ozone-platform=wayland --kiosk --disable-infobars --no-first-run http://localhost:5000
```

Make executable and run:
```bash
chmod +x ~/start_pixelparty.sh
./start_pixelparty.sh
```

## Network Setup (if needed)
For WiFi, edit:
```bash
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Add:
```
network={
    ssid="Your_WiFi_Name"
    psk="Your_WiFi_Password"
}
```

## Usage
1. SSH into Pi
2. Run the startup script or manually start Flask then Sway
3. Guests access mobile interface at: `http://[PI_IP]:5000/mobile`
4. Press `Super+Shift+Q` to exit Sway when done