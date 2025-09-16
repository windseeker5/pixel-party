#!/bin/bash

# Simple PixelParty Setup for Raspberry Pi
# Use this AFTER you have a working Raspberry Pi OS with desktop

set -e

echo "🎉 PixelParty Simple Setup"
echo "=========================="
echo ""
echo "Prerequisites:"
echo "• Raspberry Pi OS (with desktop) already installed and booting"
echo "• WiFi or Ethernet connected"
echo "• SSH enabled (optional)"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    chromium-browser \
    unclutter \
    xdotool

# Clone PixelParty if not already present
echo "📁 Setting up PixelParty..."
if [ ! -d "/home/pi/PixelParty" ]; then
    cd /home/pi
    git clone https://github.com/kdresdell/PixelParty.git
fi

cd /home/pi/PixelParty

# Create virtual environment and install dependencies
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create media directories
echo "📂 Creating media directories..."
mkdir -p media/photos media/videos media/music export

# Test PixelParty can start
echo "🧪 Testing PixelParty..."
echo "Starting PixelParty server in background..."
source venv/bin/activate
python app.py &
APP_PID=$!
sleep 5

# Check if it started
if ps -p $APP_PID > /dev/null; then
    echo "✅ PixelParty started successfully!"
    kill $APP_PID
else
    echo "❌ PixelParty failed to start"
    exit 1
fi

# Create startup script
echo "🚀 Creating startup script..."
cat > /home/pi/start-pixelparty.sh << 'EOF'
#!/bin/bash
# Start PixelParty and open in Chromium kiosk mode

cd /home/pi/PixelParty
source venv/bin/activate

# Start PixelParty in background
python app.py &
APP_PID=$!

# Wait for server to start
sleep 8

# Get IP address for display
IP_ADDRESS=$(hostname -I | awk '{print $1}')

# Start Chromium in kiosk mode
chromium-browser \
    --start-fullscreen \
    --kiosk \
    --incognito \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-translate \
    --no-first-run \
    --fast \
    --fast-start \
    --disable-features=VizDisplayCompositor \
    http://localhost:5000 &

BROWSER_PID=$!

echo "PixelParty running!"
echo "Big Screen: http://localhost:5000"
echo "Mobile: http://$IP_ADDRESS:5000/mobile"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for user to stop
trap 'echo "Stopping..."; kill $APP_PID $BROWSER_PID; exit 0' INT
wait
EOF

chmod +x /home/pi/start-pixelparty.sh

# Create mobile QR code generator
echo "📱 Creating mobile access helper..."
cat > /home/pi/show-mobile-qr.sh << 'EOF'
#!/bin/bash
# Show QR code for mobile access

IP_ADDRESS=$(hostname -I | awk '{print $1}')
MOBILE_URL="http://$IP_ADDRESS:5000/mobile"

echo "Mobile Interface URL:"
echo "$MOBILE_URL"
echo ""
echo "Generate QR code? (requires qrencode)"

if command -v qrencode >/dev/null; then
    qrencode -t ansiutf8 "$MOBILE_URL"
else
    echo "Install qrencode for QR: sudo apt install qrencode"
fi
EOF

chmod +x /home/pi/show-mobile-qr.sh

# Optional: Install QR code generator
echo "📱 Installing QR code generator (optional)..."
sudo apt install -y qrencode

# Create desktop shortcut
echo "🖥️  Creating desktop shortcut..."
cat > /home/pi/Desktop/PixelParty.desktop << 'EOF'
[Desktop Entry]
Name=PixelParty
Comment=Start PixelParty Birthday App
Exec=/home/pi/start-pixelparty.sh
Icon=/home/pi/PixelParty/app/static/favicon.ico
Terminal=true
Type=Application
Categories=Application;
EOF

chmod +x /home/pi/Desktop/PixelParty.desktop

# Final instructions
echo ""
echo "🎉 PixelParty Setup Complete!"
echo "============================="
echo ""
echo "📋 To start PixelParty:"
echo "   1. Double-click 'PixelParty' icon on desktop"
echo "   2. OR run: /home/pi/start-pixelparty.sh"
echo ""
echo "📱 For mobile QR code:"
echo "   Run: /home/pi/show-mobile-qr.sh"
echo ""
echo "🌐 Manual URLs:"
echo "   • Big Screen: http://localhost:5000"
echo "   • Mobile: http://$(hostname -I | awk '{print $1}'):5000/mobile"
echo "   • Admin: http://$(hostname -I | awk '{print $1}'):5000/admin"
echo ""
echo "🔧 Troubleshooting:"
echo "   • If screen goes black: Move mouse or press a key"
echo "   • To exit kiosk: Alt+F4 or Ctrl+C in terminal"
echo "   • Check logs: Look in terminal where you started script"
echo ""
echo "Ready for the party! 🎊"