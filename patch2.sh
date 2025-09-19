#!/bin/bash
# patch2.sh - Fix WiFi interface mapping (interfaces are swapped)
#
# PROBLEM: hostapd is configured for wlan1 but the USB WiFi is actually wlan0
# SOLUTION: Update configs to use wlan0 instead of wlan1

LOG_FILE="patch2.log"

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
    echo "Usage: sudo bash patch2.sh"
    exit 1
fi

log "Starting WiFi interface fix (patch2)"
log "Problem: hostapd configured for wlan1 but USB WiFi is wlan0"

# Step 1: Stop services
log "STEP 1: Stopping services"
run_cmd "systemctl stop hostapd" "Stop hostapd service"
run_cmd "systemctl stop dnsmasq" "Stop dnsmasq service"

# Step 2: Backup original configs
log "STEP 2: Backing up configurations"
run_cmd "cp /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.backup.$(date +%s)" "Backup hostapd config"
run_cmd "cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup.$(date +%s)" "Backup dnsmasq config"

# Step 3: Fix hostapd configuration
log "STEP 3: Fixing hostapd configuration (wlan1 -> wlan0)"
run_cmd "sed -i 's/interface=wlan1/interface=wlan0/g' /etc/hostapd/hostapd.conf" "Update hostapd interface"
run_cmd "cat /etc/hostapd/hostapd.conf" "Show updated hostapd config"

# Step 4: Fix dnsmasq configuration
log "STEP 4: Fixing dnsmasq configuration (wlan1 -> wlan0)"
run_cmd "sed -i 's/interface=wlan1/interface=wlan0/g' /etc/dnsmasq.conf" "Update dnsmasq interface"
run_cmd "grep -A5 'interface=wlan0' /etc/dnsmasq.conf" "Show updated dnsmasq config"

# Step 5: Remove old IP from wlan1 and set on wlan0
log "STEP 5: Fixing IP addresses"
run_cmd "ip addr del 192.168.4.1/24 dev wlan1" "Remove IP from wlan1 (ignore errors)"
run_cmd "ip addr add 192.168.4.1/24 dev wlan0" "Add IP to wlan0"
run_cmd "ip link set dev wlan0 up" "Bring wlan0 up"

# Step 6: Show current interface status
log "STEP 6: Checking interface status"
run_cmd "ip addr show wlan0" "Show wlan0 status"
run_cmd "ip addr show wlan1" "Show wlan1 status"
run_cmd "iwconfig" "Show wireless interface status"

# Step 7: Start services
log "STEP 7: Starting services"
run_cmd "systemctl start dnsmasq" "Start dnsmasq"
sleep 2
run_cmd "systemctl start hostapd" "Start hostapd"
sleep 3

# Step 8: Verify services are running
log "STEP 8: Verifying services"
run_cmd "systemctl status dnsmasq" "Check dnsmasq status"
run_cmd "systemctl status hostapd" "Check hostapd status"

# Step 9: Test WiFi broadcast
log "STEP 9: Testing WiFi broadcast"
run_cmd "iwconfig wlan0" "Check wlan0 wireless mode"
run_cmd "iwlist scan | grep -A5 -B5 ValerieParty" "Scan for ValerieParty network"

# Step 10: Test connectivity
log "STEP 10: Testing local connectivity"
run_cmd "ping -c 2 192.168.4.1" "Ping local IP"
run_cmd "curl -m 5 http://192.168.4.1:5001/ || echo 'Flask app not running - start manually'" "Test Flask connectivity"

# Final status
log "PATCH COMPLETED!"
log "Summary of changes:"
log "- hostapd now uses wlan0 instead of wlan1"
log "- dnsmasq now uses wlan0 instead of wlan1"
log "- IP 192.168.4.1 moved from wlan1 to wlan0"
log "- Services restarted"
log ""
log "What to do next:"
log "1. Check if 'ValerieParty' network is visible on your tablet"
log "2. If visible, connect and test http://192.168.4.1:5001/mobile/"
log "3. If not visible, check the service status above for errors"
log ""
log "Complete log saved to: $LOG_FILE"

echo ""
echo "PATCH2 COMPLETED - Check $LOG_FILE for details"
echo ""
echo "Next steps:"
echo "1. Look for 'ValerieParty' WiFi on your tablet"
echo "2. Connect and browse to: http://192.168.4.1:5001/mobile/"
echo ""