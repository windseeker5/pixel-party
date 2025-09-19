#!/bin/bash
# make_permanent.sh - Make all configurations survive reboot
#
# This script ensures that after reboot:
# 1. wlan1 gets IP 192.168.4.1 automatically
# 2. iptables rules are restored
# 3. IP forwarding is enabled
# 4. Services start correctly

LOG_FILE="make_permanent.log"

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
    echo "Usage: sudo bash make_permanent.sh"
    exit 1
fi

log "MAKING CONFIGURATIONS PERMANENT FOR REBOOT SURVIVAL"

# Step 1: Make IP forwarding permanent
log "STEP 1: Making IP forwarding permanent"
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    run_cmd "echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf" "Add IP forwarding to sysctl.conf"
else
    log "IP forwarding already permanent in sysctl.conf"
fi
run_cmd "sysctl -w net.ipv4.ip_forward=1" "Enable IP forwarding now"

# Step 2: Make wlan1 IP address permanent
log "STEP 2: Making wlan1 IP address permanent"
log "Adding static IP configuration to /etc/dhcpcd.conf"

# Remove any existing wlan1 config
run_cmd "sed -i '/^interface wlan1/,/^$/d' /etc/dhcpcd.conf" "Remove existing wlan1 config"

# Add new wlan1 static IP config
cat >> /etc/dhcpcd.conf << 'EOF'

# ValerieParty guest network configuration
interface wlan1
static ip_address=192.168.4.1/24
nohook wpa_supplicant
EOF

log "Added static IP configuration for wlan1"
run_cmd "tail -10 /etc/dhcpcd.conf" "Show dhcpcd.conf configuration"

# Step 3: Save current iptables rules
log "STEP 3: Making iptables rules permanent"
run_cmd "iptables-save > /etc/iptables.ipv4.nat" "Save current iptables rules"

# Step 4: Make iptables restore on boot
log "STEP 4: Setting up iptables restore on boot"
RESTORE_LINE="iptables-restore < /etc/iptables.ipv4.nat"

# Check if already in rc.local
if grep -q "iptables-restore" /etc/rc.local; then
    log "iptables restore already configured in rc.local"
else
    # Add before 'exit 0'
    run_cmd "sed -i '/^exit 0/i $RESTORE_LINE' /etc/rc.local" "Add iptables restore to rc.local"
    log "Added iptables restore to rc.local"
fi

run_cmd "cat /etc/rc.local" "Show rc.local content"

# Step 5: Ensure services are enabled for auto-start
log "STEP 5: Ensuring services auto-start on boot"
run_cmd "systemctl enable hostapd" "Enable hostapd auto-start"
run_cmd "systemctl enable dnsmasq" "Enable dnsmasq auto-start"

# Step 6: Create a startup script to ensure everything is set up
log "STEP 6: Creating startup validation script"
cat > /usr/local/bin/valerieparts-startup.sh << 'EOF'
#!/bin/bash
# ValerieParty startup script - ensures everything is configured correctly

LOG_FILE="/var/log/valerieparts-startup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "ValerieParty startup script running"

# Wait for network interfaces to be ready
sleep 10

# Ensure wlan1 has the correct IP
if ! ip addr show wlan1 | grep -q "192.168.4.1/24"; then
    log "Adding IP to wlan1"
    ip addr add 192.168.4.1/24 dev wlan1 2>/dev/null || true
    ip link set dev wlan1 up
fi

# Ensure IP forwarding is enabled
echo 1 > /proc/sys/net/ipv4/ip_forward

# Restore iptables if needed
if [ -f /etc/iptables.ipv4.nat ]; then
    iptables-restore < /etc/iptables.ipv4.nat
    log "iptables rules restored"
fi

# Restart services if needed
systemctl is-active --quiet dnsmasq || systemctl restart dnsmasq
systemctl is-active --quiet hostapd || systemctl restart hostapd

log "ValerieParty startup script completed"
EOF

run_cmd "chmod +x /usr/local/bin/valerieparts-startup.sh" "Make startup script executable"

# Step 7: Add startup script to systemd
log "STEP 7: Creating systemd service for startup script"
cat > /etc/systemd/system/valerieparts-startup.service << 'EOF'
[Unit]
Description=ValerieParty WiFi Startup Script
After=network.target
Wants=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/valerieparts-startup.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

run_cmd "systemctl daemon-reload" "Reload systemd"
run_cmd "systemctl enable valerieparts-startup.service" "Enable startup service"

# Step 8: Show current status
log "STEP 8: Current configuration status"
run_cmd "systemctl list-unit-files | grep -E '(hostapd|dnsmasq|valerieparts)'" "Show enabled services"
run_cmd "grep -A5 'interface wlan1' /etc/dhcpcd.conf" "Show dhcpcd wlan1 config"
run_cmd "grep 'net.ipv4.ip_forward' /etc/sysctl.conf" "Show IP forwarding config"
run_cmd "ls -la /etc/iptables.ipv4.nat" "Show iptables backup file"

log "CONFIGURATION MADE PERMANENT!"
log ""
log "What will survive reboot:"
log "✓ wlan1 will get IP 192.168.4.1 automatically (dhcpcd.conf)"
log "✓ IP forwarding enabled (sysctl.conf)"
log "✓ iptables rules restored (rc.local + startup script)"
log "✓ hostapd and dnsmasq auto-start (systemd)"
log "✓ Startup script ensures everything is correct (systemd service)"
log ""
log "Complete log saved to: $LOG_FILE"

echo ""
echo "CONFIGURATION MADE PERMANENT!"
echo ""
echo "Your Pi will now survive reboots with:"
echo "- wlan1 automatically getting IP 192.168.4.1"
echo "- Internet forwarding from wlan0 to wlan1"
echo "- ValerieParty WiFi auto-starting"
echo "- All services enabled"
echo ""
echo "Want to test reboot? Run: sudo reboot"
echo ""