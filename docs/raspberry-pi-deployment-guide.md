# 🎉 PixelParty Raspberry Pi Deployment Guide
## Simple Setup for Valerie's 50th Birthday Party

**Print this guide and follow along on your Raspberry Pi!**

---

## ⚠️ REQUIRED HARDWARE CHECKLIST

Before starting, ensure you have:
- [ ] Raspberry Pi 4 (8GB) with power supply
- [ ] **USB WiFi Adapter** (CRITICAL - find it in your stock room!)
- [ ] HDMI cable to big screen/TV
- [ ] Your phone with hotspot capability
- [ ] Another device (laptop) for SSH access

**Why USB WiFi adapter?**
- Built-in WiFi (wlan0) → Connects to your phone hotspot (internet)
- USB WiFi (wlan1) → Creates "ValerieParty" network for guests
- One WiFi card cannot do both jobs simultaneously!

---

## 📋 SETUP OVERVIEW

1. **Initial SSH Connection** (5 min)
2. **Install Required Software** (5 min)
3. **Configure Dual WiFi** (10 min)
4. **Deploy PixelParty App** (10 min)
5. **Test Complete System** (5 min)

**Total Time: ~35 minutes**

---

## 🚀 STEP 1: INITIAL CONNECTION

### 1.1 Connect to Raspberry Pi via SSH
```bash
# From your Linux laptop
ssh pi@[your-raspberry-pi-ip-address]
```
- [ ] Successfully connected to Pi via SSH
- [ ] Can see Pi command prompt

### 1.2 Update System (Optional but Recommended)
```bash
sudo apt update
sudo apt upgrade -y
```
- [ ] System updated successfully

---

## 📦 STEP 2: INSTALL REQUIRED SOFTWARE

### 2.1 Install Network Services
```bash
sudo apt install -y hostapd dnsmasq
```
- [ ] hostapd installed (creates WiFi access point)
- [ ] dnsmasq installed (DHCP server for guests)

### 2.2 Stop Services During Configuration
```bash
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
```
- [ ] Services stopped for configuration

---

## 📡 STEP 3: CONFIGURE DUAL WIFI

### 3.1 Check WiFi Interfaces
```bash
iwconfig
```
**Expected Output:**
- `wlan0` - Built-in WiFi (should be connected to your phone hotspot)
- `wlan1` - USB WiFi adapter

- [ ] Both wlan0 and wlan1 are visible
- [ ] wlan0 is connected to your phone hotspot

**🛑 STOP HERE if you don't see wlan1!**
→ USB WiFi adapter not detected
→ Try different USB port or find another adapter

### 3.2 Configure Guest Access Point
```bash
sudo nano /etc/hostapd/hostapd.conf
```

**Copy this EXACTLY into the file:**
```
interface=wlan1
driver=nl80211
ssid=ValerieParty
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
```

**Save and exit:** Ctrl+X, then Y, then Enter

- [ ] hostapd.conf file created with correct content

### 3.3 Configure DHCP for Guests
```bash
sudo nano /etc/dnsmasq.conf
```

**Add these lines to the END of the file:**
```
# PixelParty Guest Network
interface=wlan1
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
address=/#/192.168.4.1
```

**Save and exit:** Ctrl+X, then Y, then Enter

- [ ] dnsmasq.conf configured for guest network

### 3.4 Set Static IP for Guest Network
```bash
sudo ip addr add 192.168.4.1/24 dev wlan1
sudo ip link set dev wlan1 up
```
- [ ] Static IP assigned to guest network interface

---

## 🎯 STEP 4: DEPLOY PIXELPARTY APP

### 4.1 Copy Application to Pi
**From your Linux laptop (new terminal):**
```bash
scp -r /home/kdresdell/Documents/DEV/PixelParty pi@[pi-ip]:~/
```
- [ ] PixelParty app copied to Raspberry Pi

### 4.2 Install Python Dependencies
**Back on Pi SSH session:**
```bash
cd ~/PixelParty
pip install flask pillow qrcode mutagen requests
```
- [ ] Python dependencies installed

### 4.3 Create Media Directories
```bash
mkdir -p media/photos media/videos media/music
chmod 755 media media/photos media/videos media/music
```
- [ ] Media directories created with correct permissions

### 4.4 Test App Locally
```bash
python app.py
```
**Expected output:** Flask development server starting on port 5000

**Press Ctrl+C to stop** (we'll start it properly next)

- [ ] App starts without errors
- [ ] Flask server runs on port 5000

---

## 🔧 STEP 5: START ALL SERVICES

### 5.1 Start Network Services
```bash
sudo systemctl start hostapd
sudo systemctl start dnsmasq
```

### 5.2 Check Service Status
```bash
sudo systemctl status hostapd
sudo systemctl status dnsmasq
```
**Both should show "active (running)" in green**

- [ ] hostapd service running
- [ ] dnsmasq service running

### 5.3 Enable Services for Auto-Start
```bash
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
```
- [ ] Services will start automatically on reboot

### 5.4 Start PixelParty App
```bash
cd ~/PixelParty
nohup python app.py > app.log 2>&1 &
```
- [ ] PixelParty app running in background
- [ ] App log file created (app.log)

---

## 🧪 STEP 6: COMPLETE SYSTEM TEST

### 6.1 Check Guest WiFi Network
**On your phone:**
1. Look for WiFi network "ValerieParty"
2. Connect to it (no password required)
3. Phone should get IP like 192.168.4.x

- [ ] "ValerieParty" network visible on phone
- [ ] Phone connects successfully
- [ ] Phone gets IP address from Pi

### 6.2 Test Mobile Interface
**On connected phone, open browser to:**
```
http://192.168.4.1:5000/mobile
```

- [ ] Mobile interface loads correctly
- [ ] Can see photo upload form
- [ ] Can see wish text input

### 6.3 Test Photo Upload
1. Select a test photo
2. Enter your name
3. Write a birthday wish
4. Submit

- [ ] Photo uploads successfully
- [ ] Success message appears
- [ ] No error messages

### 6.4 Test Big Screen Display
**On Pi, open Chromium:**
```bash
DISPLAY=:0 chromium --kiosk --disable-gpu-sandbox http://localhost:5000/display &
```

- [ ] Big screen shows slideshow
- [ ] Test photo appears with wish text overlay
- [ ] Display updates automatically

---

## 🎊 STEP 7: PARTY MODE SETUP

### 7.1 Generate QR Code for Guests
**The app automatically generates QR codes that include:**
- WiFi connection to "ValerieParty"
- Direct link to mobile interface

**Display QR code on screen by visiting:**
```
http://localhost:5000/qr
```

- [ ] QR code displays correctly
- [ ] Code includes WiFi + URL information

### 7.2 Final Performance Check
```bash
# Check memory usage
free -h

# Check running processes
top

# Check network interfaces
iwconfig
```

**Verify:**
- [ ] Memory usage under 80%
- [ ] Both WiFi interfaces active
- [ ] No error processes

---

## 🚨 TROUBLESHOOTING

### Problem: USB WiFi not detected
**Solution:**
```bash
lsusb  # Check if USB device visible
dmesg | tail  # Check for driver messages
```
- Try different USB port
- Some adapters need specific drivers

### Problem: "ValerieParty" network not visible
**Check:**
```bash
sudo systemctl status hostapd
sudo journalctl -u hostapd
```
- Ensure wlan1 interface is up
- Check hostapd.conf for typos

### Problem: Guests can't access app
**Check:**
```bash
sudo systemctl status dnsmasq
netstat -tlnp | grep 5000
```
- Verify dnsmasq is running
- Check Flask app is listening on all interfaces

### Problem: App won't start
**Check logs:**
```bash
cd ~/PixelParty
cat app.log
python app.py  # Run in foreground to see errors
```

### Problem: Out of memory
**Free up memory:**
```bash
# Stop Ollama temporarily if needed
sudo systemctl stop ollama

# Check what's using memory
ps aux --sort=-%mem | head
```

---

## 📞 ERROR REPORTING TO CLAUDE

### When Something Goes Wrong:

1. **Capture the exact error:**
```bash
# For app errors
cat ~/PixelParty/app.log

# For service errors
sudo journalctl -u hostapd -n 20
sudo journalctl -u dnsmasq -n 20

# For system errors
dmesg | tail
```

2. **Copy the output and paste it when messaging Claude**

3. **Include what you were trying to do:**
   - "I was trying to start hostapd and got this error..."
   - "The mobile interface won't load and here's the app.log..."

### Quick Status Check Commands:
```bash
# Network status
iwconfig
ip addr show

# Service status
sudo systemctl status hostapd dnsmasq

# App status
ps aux | grep python
netstat -tlnp | grep 5000

# Memory status
free -h
```

---

## ✅ SUCCESS CHECKLIST

**Your PixelParty is ready when:**
- [ ] Phone connects to "ValerieParty" WiFi automatically
- [ ] Mobile interface loads at 192.168.4.1:5000/mobile
- [ ] Photos upload successfully from phone
- [ ] Big screen shows slideshow with text overlays
- [ ] QR code displays for easy guest access
- [ ] System remains responsive with Ollama running
- [ ] Services auto-start after reboot

**🎉 Party time! Let guests scan the QR code and start sharing memories!**

---

## 🔄 QUICK RESTART COMMANDS

**If you need to restart everything:**
```bash
# Restart network services
sudo systemctl restart hostapd dnsmasq

# Restart PixelParty app
cd ~/PixelParty
pkill -f python
nohup python app.py > app.log 2>&1 &

# Restart big screen display
pkill chromium
DISPLAY=:0 chromium --kiosk --disable-gpu-sandbox http://localhost:5000/display &
```

---

*This guide was created specifically for Valerie's 50th birthday party PixelParty setup. Keep it simple, keep it working!*