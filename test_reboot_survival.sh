#!/bin/bash
# test_reboot_survival.sh - Test if configuration will survive reboot
#
# This script checks if all configurations are properly saved
# Run BEFORE rebooting to validate everything will work

LOG_FILE="reboot_test.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_config() {
    local desc="$1"
    local check_cmd="$2"
    local expected="$3"

    log "Checking: $desc"
    local result=$(eval "$check_cmd" 2>/dev/null)

    if echo "$result" | grep -q "$expected"; then
        log "✓ PASS: $desc"
        return 0
    else
        log "✗ FAIL: $desc"
        log "   Expected: $expected"
        log "   Got: $result"
        return 1
    fi
}

log "TESTING REBOOT SURVIVAL CONFIGURATION"
log "This checks if everything will work after reboot"
log ""

passed=0
failed=0

# Test 1: IP forwarding permanent
if check_config "IP forwarding in sysctl.conf" "grep 'net.ipv4.ip_forward=1' /etc/sysctl.conf" "net.ipv4.ip_forward=1"; then
    ((passed++))
else
    ((failed++))
fi

# Test 2: wlan1 static IP in dhcpcd
if check_config "wlan1 static IP in dhcpcd.conf" "grep -A3 'interface wlan1' /etc/dhcpcd.conf" "static ip_address=192.168.4.1/24"; then
    ((passed++))
else
    ((failed++))
fi

# Test 3: iptables rules saved
if check_config "iptables rules saved" "ls /etc/iptables.ipv4.nat" "iptables.ipv4.nat"; then
    ((passed++))
else
    ((failed++))
fi

# Test 4: iptables restore in rc.local
if check_config "iptables restore in rc.local" "grep 'iptables-restore' /etc/rc.local" "iptables-restore"; then
    ((passed++))
else
    ((failed++))
fi

# Test 5: hostapd enabled
if check_config "hostapd service enabled" "systemctl is-enabled hostapd" "enabled"; then
    ((passed++))
else
    ((failed++))
fi

# Test 6: dnsmasq enabled
if check_config "dnsmasq service enabled" "systemctl is-enabled dnsmasq" "enabled"; then
    ((passed++))
else
    ((failed++))
fi

# Test 7: hostapd config correct
if check_config "hostapd uses wlan1" "grep 'interface=wlan1' /etc/hostapd/hostapd.conf" "interface=wlan1"; then
    ((passed++))
else
    ((failed++))
fi

# Test 8: dnsmasq config correct
if check_config "dnsmasq uses wlan1" "grep 'interface=wlan1' /etc/dnsmasq.conf" "interface=wlan1"; then
    ((passed++))
else
    ((failed++))
fi

# Test 9: startup script exists
if check_config "startup script exists" "ls /usr/local/bin/valerieparts-startup.sh" "valerieparts-startup.sh"; then
    ((passed++))
else
    ((failed++))
fi

# Test 10: startup service enabled
if check_config "startup service enabled" "systemctl is-enabled valerieparts-startup.service" "enabled"; then
    ((passed++))
else
    ((failed++))
fi

log ""
log "REBOOT SURVIVAL TEST RESULTS:"
log "✓ Passed: $passed"
log "✗ Failed: $failed"
log ""

if [ $failed -eq 0 ]; then
    log "🎉 ALL TESTS PASSED!"
    log "Your configuration WILL survive reboot."
    log "It's safe to run: sudo reboot"
    echo ""
    echo "🎉 ALL TESTS PASSED! Safe to reboot."
    exit 0
else
    log "❌ SOME TESTS FAILED!"
    log "Run 'sudo bash make_permanent.sh' to fix issues."
    echo ""
    echo "❌ TESTS FAILED! Run make_permanent.sh first."
    exit 1
fi