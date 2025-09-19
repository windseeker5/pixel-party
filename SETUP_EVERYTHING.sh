#!/bin/bash
# SETUP_EVERYTHING.sh - ONE SCRIPT TO RULE THEM ALL
#
# This script sets up EVERYTHING for PixelParty from scratch:
# - wlan0: Connected to Kitesurfer (your phone hotspot)
# - wlan1: Broadcasting ValerieParty (guest network)
# - IP forwarding from wlan0 to wlan1 (internet for guests)
# - DHCP for guests (192.168.4.2-254)
# - DNS redirection to your app
# - All services running
#
# RUN THIS AFTER EVERY REBOOT OR WHEN SHIT BREAKS

LOG_FILE="SETUP_EVERYTHING.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

run_cmd() {
    local cmd="$1"
    local desc="$2"
    log "Running: $desc"
    log "Command: $cmd"
    eval "$cmd" 2>&1 | tee -a "$LOG_FILE"
    local exit_code=${PIPESTATUS[0]}
    log "Exit code: $exit_code"
    return $exit_code
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash SETUP_EVERYTHING.sh"
    exit 1
fi

echo "🚀 SETTING UP PIXELPARTY NETWORK - ONE SCRIPT TO RULE THEM ALL"
log "Starting complete PixelParty network setup"
log "Target: wlan0=Kitesurfer, wlan1=ValerieParty with internet forwarding"

# STEP 1: STOP ALL SERVICES
log "🛑 STEP 1: Stopping all services"
run_cmd "systemctl stop hostapd" "Stop hostapd"
run_cmd "systemctl stop dnsmasq" "Stop dnsmasq"
run_cmd "pkill -f hostapd" "Kill any remaining hostapd processes"
run_cmd "pkill -f dnsmasq" "Kill any remaining dnsmasq processes"

# STEP 2: CLEAN UP INTERFACES
log "🧹 STEP 2: Cleaning up network interfaces"
run_cmd "ip addr flush dev wlan1" "Flush wlan1 addresses"
run_cmd "ip link set dev wlan1 down" "Bring wlan1 down"
run_cmd "ip link set dev wlan1 up" "Bring wlan1 up"

# STEP 3: SET UP WLAN1 INTERFACE
log "🔧 STEP 3: Setting up wlan1 interface"
run_cmd "ip addr add 192.168.4.1/24 dev wlan1" "Add IP to wlan1"
run_cmd "ip link set dev wlan1 up" "Ensure wlan1 is up"

# STEP 4: ENABLE IP FORWARDING
log "🔀 STEP 4: Enabling IP forwarding"
run_cmd "sysctl -w net.ipv4.ip_forward=1" "Enable IP forwarding"

# STEP 5: SET UP IPTABLES RULES
log "🛡️ STEP 5: Setting up iptables rules"
# Clear existing rules
run_cmd "iptables -t nat -F" "Flush NAT table"
run_cmd "iptables -F FORWARD" "Flush FORWARD chain"

# Set up NAT and forwarding
run_cmd "iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE" "Set up NAT masquerading"
run_cmd "iptables -A FORWARD -i wlan1 -o wlan0 -j ACCEPT" "Allow forward wlan1->wlan0"
run_cmd "iptables -A FORWARD -i wlan0 -o wlan1 -m state --state RELATED,ESTABLISHED -j ACCEPT" "Allow return traffic"

# STEP 6: CONFIGURE HOSTAPD
log "📡 STEP 6: Configuring hostapd"
cat > /etc/hostapd/hostapd.conf << 'EOF'
interface=wlan1
driver=nl80211
ssid=ValerieParty
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
EOF
run_cmd "cat /etc/hostapd/hostapd.conf" "Show hostapd config"

# STEP 7: CONFIGURE DNSMASQ
log "🌐 STEP 7: Configuring dnsmasq"
# Backup original
run_cmd "cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup.$(date +%s)" "Backup dnsmasq config"

# Remove any existing PixelParty config
run_cmd "sed -i '/# PixelParty Guest Network/,/^$/d' /etc/dnsmasq.conf" "Remove old PixelParty config"

# Add new config
cat >> /etc/dnsmasq.conf << 'EOF'

# PixelParty Guest Network
interface=wlan1
dhcp-range=192.168.4.2,192.168.4.254,255.255.255.0,24h
address=/#/192.168.4.1
EOF

run_cmd "tail -10 /etc/dnsmasq.conf" "Show dnsmasq config"

# STEP 8: START SERVICES
log "🚀 STEP 8: Starting services"
run_cmd "systemctl start dnsmasq" "Start dnsmasq"
sleep 3
run_cmd "systemctl start hostapd" "Start hostapd"
sleep 5

# STEP 9: VERIFY EVERYTHING
log "✅ STEP 9: Verifying setup"
run_cmd "systemctl status dnsmasq" "Check dnsmasq status"
run_cmd "systemctl status hostapd" "Check hostapd status"
run_cmd "iwconfig" "Check wireless interfaces"
run_cmd "ip addr show" "Check IP addresses"
run_cmd "iptables -t nat -L POSTROUTING" "Check NAT rules"
run_cmd "iptables -L FORWARD" "Check forward rules"

# STEP 10: TEST CONNECTIVITY
log "🧪 STEP 10: Testing connectivity"
run_cmd "ping -c 2 192.168.4.1" "Test local IP"
run_cmd "iwlist scan | grep -A3 -B3 ValerieParty || echo 'ValerieParty not found'" "Scan for ValerieParty"

# STEP 11: FINAL STATUS
log "📊 STEP 11: Final status check"
wlan0_ip=$(ip addr show wlan0 | grep "inet " | awk '{print $2}' | head -1)
wlan1_ip=$(ip addr show wlan1 | grep "inet " | awk '{print $2}' | head -1)
hostapd_status=$(systemctl is-active hostapd)
dnsmasq_status=$(systemctl is-active dnsmasq)

log "=== SETUP COMPLETE ==="
log "wlan0 (Kitesurfer): $wlan0_ip"
log "wlan1 (ValerieParty): $wlan1_ip"
log "hostapd: $hostapd_status"
log "dnsmasq: $dnsmasq_status"

echo ""
echo "🎉 PIXELPARTY NETWORK SETUP COMPLETE!"
echo ""
echo "Network Status:"
echo "- wlan0 (Kitesurfer hotspot): $wlan0_ip"
echo "- wlan1 (ValerieParty guests): $wlan1_ip"
echo "- hostapd: $hostapd_status"
echo "- dnsmasq: $dnsmasq_status"
echo ""

if [ "$hostapd_status" = "active" ] && [ "$dnsmasq_status" = "active" ] && [ "$wlan1_ip" = "192.168.4.1/24" ]; then
    echo "✅ SUCCESS! Everything is working!"
    echo ""
    echo "What guests should do:"
    echo "1. Connect to 'ValerieParty' WiFi"
    echo "2. Open browser to: http://192.168.4.1:5001/mobile/"
    echo ""
    echo "Next: Start your Flask app with:"
    echo "cd /home/kdresdell/Documents/DEV/PixelParty"
    echo "python app.py"
else
    echo "❌ SOMETHING IS WRONG! Check the log: $LOG_FILE"
fi

echo ""
echo "Complete log saved to: $LOG_FILE"
echo ""