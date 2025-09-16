# Zero-Configuration WiFi Solution for PixelParty
## Ski Resort Birthday Party Network Setup

### Challenge
- Party location: Ski resort with no WiFi infrastructure
- Need: Guest access to mobile interface without configuration
- Constraint: Guests may be non-technical or intoxicated
- Goal: Scan QR code → Instant access, no manual WiFi setup

---

## Option 1: WiFi QR Code with Auto-Connect (Simplest)

### How It Works
Embed WiFi credentials directly in the QR code. Modern phones auto-connect when scanning.

### Setup Steps
1. Create an open WiFi network (no password) on router or phone hotspot
2. Generate special WiFi QR format:
   ```
   WIFI:T:OPEN;S:PartyWiFi;P:;H:false;;
   ```
3. After connection, redirect to: `http://192.168.1.x:5000/mobile`

### Implementation
- Modify `app/services/qr_generator.py` to generate WiFi QR codes
- Add fallback standard URL QR for older devices
- Display both QR codes on welcome screen

### Pros
- Works with most modern smartphones
- No additional hardware needed
- Quick to implement

### Cons
- Some older phones don't support WiFi QR
- Still requires manual connection on some devices

---

## Option 2: Captive Portal Solution (Most Seamless)

### How It Works
Create an open WiFi that automatically redirects to your app when guests connect.

### Setup Steps
1. Configure router as access point with captive portal
2. Set SSID to "ValerieParty" (open, no password)
3. Configure DNS to redirect all traffic to Raspberry Pi
4. Any HTTP request opens mobile interface automatically

### Implementation
- Add captive portal detection endpoint (`/generate_204`, `/hotspot-detect.html`)
- Configure router DNS settings to point to Pi IP
- Add portal detection responses to Flask app
- Modify nginx/Apache if using reverse proxy

### Pros
- Most seamless experience - just connect to WiFi
- Works like hotel/airport WiFi
- No QR scanning needed after connection

### Cons
- Requires router configuration
- May need specific router model
- Some phones cache DNS

---

## Option 3: Raspberry Pi as Access Point (Most Reliable)

### How It Works
Raspberry Pi becomes the WiFi access point itself - no external router needed.

### Setup Steps
1. Install required packages:
   ```bash
   sudo apt-get install hostapd dnsmasq iptables-persistent
   ```

2. Configure hostapd (`/etc/hostapd/hostapd.conf`):
   ```
   interface=wlan0
   driver=nl80211
   ssid=ValerieParty
   hw_mode=g
   channel=7
   wmm_enabled=0
   macaddr_acl=0
   auth_algs=1
   ignore_broadcast_ssid=0
   ```

3. Configure dnsmasq (`/etc/dnsmasq.conf`):
   ```
   interface=wlan0
   dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
   address=/#/192.168.4.1
   ```

4. Set up network routing and NAT

### Implementation
- Create setup script: `setup/configure_ap.sh`
- Add systemd service for auto-start
- Configure iptables for traffic redirection
- Update Flask app to detect AP mode

### Pros
- Complete control over network
- No external dependencies
- Works in any location
- Most reliable solution

### Cons
- More complex setup
- Pi's WiFi chip may have range limitations
- Need USB WiFi adapter for better performance

---

## RECOMMENDED: Hybrid Solution (Option 1 + 3)

### Why This Combination?
- **Primary**: Pi as access point (reliable, no dependencies)
- **Enhancement**: WiFi QR for instant connection
- **Fallback**: Standard URL QR for manual connection

### Implementation Plan

#### Phase 1: Configure Pi as Access Point
```bash
#!/bin/bash
# setup/configure_ap.sh

# Install packages
sudo apt-get update
sudo apt-get install -y hostapd dnsmasq iptables-persistent

# Configure network interface
sudo tee /etc/dhcpcd.conf > /dev/null <<EOF
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF

# Configure hostapd
sudo tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=wlan0
driver=nl80211
ssid=ValerieParty
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
EOF

# Configure dnsmasq
sudo tee /etc/dnsmasq.conf > /dev/null <<EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
# Redirect all DNS to Pi
address=/#/192.168.4.1
EOF

# Enable IP forwarding
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf

# Configure NAT
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT

# Save iptables rules
sudo netfilter-persistent save

# Enable services
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

echo "Access point configured! Reboot to activate."
```

#### Phase 2: Update QR Generator
```python
# app/services/qr_generator.py modifications

def generate_wifi_qr(ssid: str, password: str = "", auth_type: str = "nopass") -> str:
    """Generate WiFi QR code that auto-connects phones."""
    if auth_type == "nopass":
        wifi_string = f"WIFI:T:nopass;S:{ssid};P:;H:false;;"
    else:
        wifi_string = f"WIFI:T:WPA;S:{ssid};P:{password};H:false;;"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(wifi_string)
    qr.make(fit=True)

    # Convert to base64 data URI
    img = qr.make_image(fill_color="black", back_color="white")
    # ... rest of conversion code
    return data_uri

def generate_dual_qr(network_ip: str, port: int = 5000) -> dict:
    """Generate both WiFi and URL QR codes."""
    return {
        'wifi_qr': generate_wifi_qr("ValerieParty"),
        'url_qr': generate_qr_code(f"http://{network_ip}:{port}/mobile"),
        'mobile_url': f"http://{network_ip}:{port}/mobile"
    }
```

#### Phase 3: Add Captive Portal Detection
```python
# app/routes/api.py additions

@api_bp.route('/generate_204')
@api_bp.route('/hotspot-detect.html')
@api_bp.route('/connecttest.txt')
def captive_portal_detect():
    """Handle captive portal detection from various devices."""
    # Redirect to mobile interface
    return redirect('/mobile', code=302)

@api_bp.route('/success.txt')
def captive_success():
    """Some devices check for this after connection."""
    return 'success\n'
```

#### Phase 4: Update Network Utils
```python
# app/utils/network_utils.py modifications

def detect_ap_mode():
    """Detect if running in access point mode."""
    try:
        import subprocess
        result = subprocess.run(['systemctl', 'is-active', 'hostapd'],
                              capture_output=True, text=True)
        return result.stdout.strip() == 'active'
    except:
        return False

def get_ap_network_info():
    """Get network info when in AP mode."""
    if detect_ap_mode():
        return {
            'network_ip': '192.168.4.1',
            'ssid': 'ValerieParty',
            'mode': 'access_point'
        }
    else:
        return {
            'network_ip': get_network_ip(),
            'ssid': None,
            'mode': 'client'
        }
```

#### Phase 5: Update Display Template
```javascript
// templates/big_screen/display.html modifications

function generateQRCode() {
    fetch('/api/network_info')
        .then(response => response.json())
        .then(data => {
            // Generate WiFi QR if in AP mode
            if (data.mode === 'access_point') {
                // Show WiFi QR prominently
                generateWiFiQR(data.ssid);
                // Show instructions
                showAPInstructions();
            }
            // Always show URL QR as fallback
            generateURLQR(data.mobile_url);
        });
}

function showAPInstructions() {
    const instructions = document.createElement('div');
    instructions.innerHTML = `
        <div class="text-center mt-4">
            <p class="text-lg font-bold">Option 1: Scan QR with camera</p>
            <p class="text-sm">Auto-connects to WiFi + Opens app</p>
            <div class="divider">OR</div>
            <p class="text-lg font-bold">Option 2: Manual connection</p>
            <p class="text-sm">1. Connect to WiFi: "ValerieParty"</p>
            <p class="text-sm">2. Open any website - auto-redirects</p>
        </div>
    `;
    document.getElementById('connection-instructions').appendChild(instructions);
}
```

### Testing Checklist
- [ ] Pi successfully creates "ValerieParty" WiFi network
- [ ] Devices can connect without password
- [ ] QR code auto-connects phones to WiFi
- [ ] Any web request redirects to mobile interface
- [ ] Mobile interface loads correctly at 192.168.4.1:5000
- [ ] Photos upload successfully
- [ ] Music requests work
- [ ] Multiple devices can connect simultaneously
- [ ] Network remains stable under load

### Deployment Day Checklist
1. **Night Before**:
   - [ ] Test complete setup at home
   - [ ] Charge all devices
   - [ ] Download offline backup of all dependencies
   - [ ] Test with multiple phones

2. **Equipment to Bring**:
   - [ ] Raspberry Pi 4 with configured SD card
   - [ ] Backup SD card with same setup
   - [ ] USB WiFi adapter (for better range)
   - [ ] Ethernet cable (backup connection)
   - [ ] Power bank for Pi (backup power)
   - [ ] HDMI cable for debugging

3. **At Venue**:
   - [ ] Power on Pi 30 minutes before party
   - [ ] Verify "ValerieParty" network visible
   - [ ] Test with your phone first
   - [ ] Display QR codes on big screen
   - [ ] Have manual instructions ready as backup

### Troubleshooting Guide

**Issue**: WiFi network not visible
- Check: `sudo systemctl status hostapd`
- Fix: `sudo systemctl restart hostapd`

**Issue**: Devices connect but no internet
- This is expected! App works locally
- Ensure dnsmasq redirects to Pi

**Issue**: QR code not auto-connecting
- Fallback: Display network name prominently
- Have guests manually connect to "ValerieParty"

**Issue**: Poor WiFi range
- Use USB WiFi adapter instead of built-in
- Position Pi centrally in party area
- Reduce channel congestion (change channel in hostapd.conf)

### Performance Optimization
- Limit concurrent connections in hostapd (max 20 devices)
- Pre-cache all static assets
- Optimize image sizes before party
- Use local CDN copies of all JavaScript/CSS

### Success Metrics
- Zero guest configuration required ✓
- Works with intoxicated users ✓
- No internet dependency ✓
- Instant access via QR scan ✓
- Fallback options available ✓

---

## Final Notes
This solution prioritizes **simplicity for guests** over technical elegance. The hybrid approach ensures maximum compatibility while maintaining the zero-configuration goal. The Pi as AP eliminates external dependencies, making it perfect for a remote ski resort location.

Remember: The goal is for guests to access the app with minimal friction, allowing them to focus on celebrating Valérie's 50th birthday!