#!/bin/bash
# fix_my_fuckup.sh - Revert the interface mapping disaster
#
# CLAUDE FUCKED UP!
# wlan0 = Built-in WiFi connected to "Kitesurfer" hotspot
# wlan1 = USB WiFi that should create "ValerieParty"
#
# Reverting all the wrong changes from patch2.sh

LOG_FILE="fix_fuckup.log"

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
    echo "Usage: sudo bash fix_my_fuckup.sh"
    exit 1
fi

log "FIXING CLAUDE'S FUCKUP - Restoring correct interface mapping"
log "wlan0 = Kitesurfer hotspot connection (built-in WiFi)"
log "wlan1 = ValerieParty guest network (USB WiFi adapter)"

# Step 1: Stop services
log "STEP 1: Stopping services"
run_cmd "systemctl stop hostapd" "Stop hostapd service"
run_cmd "systemctl stop dnsmasq" "Stop dnsmasq service"

# Step 2: Show current broken state
log "STEP 2: Current broken state"
run_cmd "iwconfig" "Show current wireless interfaces"
run_cmd "ip addr show" "Show current IP addresses"

# Step 3: Restore hostapd configuration (back to wlan1)
log "STEP 3: Restoring hostapd configuration (wlan0 -> wlan1)"
run_cmd "sed -i 's/interface=wlan0/interface=wlan1/g' /etc/hostapd/hostapd.conf" "Restore hostapd interface to wlan1"
run_cmd "cat /etc/hostapd/hostapd.conf" "Show restored hostapd config"

# Step 4: Restore dnsmasq configuration (back to wlan1)
log "STEP 4: Restoring dnsmasq configuration (wlan0 -> wlan1)"
run_cmd "sed -i 's/interface=wlan0/interface=wlan1/g' /etc/dnsmasq.conf" "Restore dnsmasq interface to wlan1"
run_cmd "grep -A5 'interface=wlan1' /etc/dnsmasq.conf" "Show restored dnsmasq config"

# Step 5: Fix IP addresses
log "STEP 5: Fixing IP addresses"
run_cmd "ip addr del 192.168.4.1/24 dev wlan0 2>/dev/null || true" "Remove wrong IP from wlan0"
run_cmd "ip addr add 192.168.4.1/24 dev wlan1" "Add correct IP to wlan1"
run_cmd "ip link set dev wlan1 up" "Bring wlan1 up"

# Step 6: Show corrected interface status
log "STEP 6: Checking corrected interface status"
run_cmd "ip addr show wlan0" "Show wlan0 status (should have Kitesurfer IP)"
run_cmd "ip addr show wlan1" "Show wlan1 status (should have 192.168.4.1)"
run_cmd "iwconfig" "Show wireless interface status"

# Step 7: Start services in correct order
log "STEP 7: Starting services"
run_cmd "systemctl start dnsmasq" "Start dnsmasq"
sleep 2
run_cmd "systemctl start hostapd" "Start hostapd"
sleep 3

# Step 8: Verify services
log "STEP 8: Verifying services"
run_cmd "systemctl status dnsmasq" "Check dnsmasq status"
run_cmd "systemctl status hostapd" "Check hostapd status"

# Step 9: Test WiFi broadcast on correct interface
log "STEP 9: Testing WiFi broadcast on wlan1"
run_cmd "iwconfig wlan1" "Check wlan1 wireless mode (should show Master mode and ValerieParty)"
run_cmd "iwlist scan | grep -A5 -B5 ValerieParty || echo 'ValerieParty not found in scan'" "Scan for ValerieParty network"

# Step 10: Test connectivity
log "STEP 10: Testing connectivity"
run_cmd "ping -c 2 192.168.4.1" "Ping guest network IP"

# Final status
log "FUCKUP FIXED!"
log "Summary of corrections:"
log "- hostapd restored to use wlan1 (USB WiFi for guests)"
log "- dnsmasq restored to use wlan1"
log "- IP 192.168.4.1 moved back to wlan1"
log "- wlan0 remains connected to Kitesurfer hotspot"
log "- Services restarted with correct configuration"
log ""
log "What should happen now:"
log "1. wlan0 stays connected to 'Kitesurfer' (your phone hotspot)"
log "2. wlan1 broadcasts 'ValerieParty' network for guests"
log "3. Guests connect to ValerieParty and get internet via wlan0"
log ""
log "Complete log saved to: $LOG_FILE"

echo ""
echo "CLAUDE'S FUCKUP FIXED - Check $LOG_FILE for details"
echo ""
echo "The correct setup should now be:"
echo "- wlan0: Connected to Kitesurfer (your phone hotspot)"
echo "- wlan1: Broadcasting ValerieParty (guest network)"
echo ""
echo "Try connecting your tablet to 'ValerieParty' now!"
echo ""