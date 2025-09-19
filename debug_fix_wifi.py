#!/usr/bin/env python3
"""
ValerieParty WiFi Debug & Fix Script
Diagnoses and fixes all WiFi issues with detailed logging
Run this when shit breaks!
"""

import subprocess
import sys
import os
import datetime
import time

# Configuration
LOG_FILE = "wifi_debug.log"
GUEST_INTERFACE = "wlan1"
GUEST_IP = "192.168.4.1"

def log_message(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {level}: {message}"
    print(log_entry)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

def run_command(command, description, ignore_errors=False, capture=True):
    """Run command and log everything"""
    log_message(f"Running: {description}")
    log_message(f"Command: {command}")

    try:
        if capture:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            log_message(f"Exit code: {result.returncode}")
            if result.stdout:
                log_message(f"STDOUT: {result.stdout.strip()}")
            if result.stderr:
                log_message(f"STDERR: {result.stderr.strip()}")

            if result.returncode != 0 and not ignore_errors:
                log_message(f"ERROR: Command failed: {command}", "ERROR")
                return False, result.stdout, result.stderr
            return True, result.stdout, result.stderr
        else:
            # For commands that need real-time output
            result = subprocess.run(command, shell=True, timeout=30)
            log_message(f"Exit code: {result.returncode}")
            return result.returncode == 0, "", ""

    except subprocess.TimeoutExpired:
        log_message(f"ERROR: Command timed out: {command}", "ERROR")
        return False, "", "TIMEOUT"
    except Exception as e:
        log_message(f"ERROR: Exception running command: {e}", "ERROR")
        return False, "", str(e)

def check_system_status():
    """Check current system status"""
    log_message("=== CHECKING SYSTEM STATUS ===")

    # Check if running as root
    if os.geteuid() != 0:
        log_message("ERROR: Script must be run with sudo", "ERROR")
        return False

    # Check WiFi interfaces
    success, stdout, stderr = run_command("iwconfig", "Check WiFi interfaces")

    # Check IP addresses
    run_command("ip addr show", "Check IP addresses")

    # Check routing
    run_command("ip route show", "Check routing table")

    # Check if wlan1 has IP
    success, stdout, stderr = run_command(f"ip addr show {GUEST_INTERFACE}", "Check wlan1 IP")
    if "192.168.4.1" not in stdout:
        log_message(f"ERROR: {GUEST_INTERFACE} missing IP address", "ERROR")
        return False

    log_message("System status check completed")
    return True

def check_services():
    """Check service status"""
    log_message("=== CHECKING SERVICES ===")

    # Check hostapd
    success, stdout, stderr = run_command("systemctl status hostapd", "Check hostapd status", ignore_errors=True)
    if "active (running)" not in stdout:
        log_message("ERROR: hostapd not running", "ERROR")
        run_command("journalctl -u hostapd -n 20", "Get hostapd logs")
        return False

    # Check dnsmasq
    success, stdout, stderr = run_command("systemctl status dnsmasq", "Check dnsmasq status", ignore_errors=True)
    if "active (running)" not in stdout:
        log_message("ERROR: dnsmasq not running", "ERROR")
        run_command("journalctl -u dnsmasq -n 20", "Get dnsmasq logs")
        return False

    log_message("All services are running")
    return True

def fix_wlan1_interface():
    """Fix wlan1 interface configuration"""
    log_message("=== FIXING WLAN1 INTERFACE ===")

    # Check current state
    success, stdout, stderr = run_command(f"ip addr show {GUEST_INTERFACE}", "Check current wlan1 state")

    # Remove existing IP if present
    if "192.168.4.1" in stdout:
        log_message("IP already present, removing first")
        run_command(f"ip addr del {GUEST_IP}/24 dev {GUEST_INTERFACE}", "Remove existing IP", ignore_errors=True)

    # Bring interface down and up
    run_command(f"ip link set dev {GUEST_INTERFACE} down", "Bring wlan1 down")
    time.sleep(2)
    run_command(f"ip link set dev {GUEST_INTERFACE} up", "Bring wlan1 up")
    time.sleep(2)

    # Set IP address
    success, stdout, stderr = run_command(f"ip addr add {GUEST_IP}/24 dev {GUEST_INTERFACE}", "Set wlan1 IP address")
    if not success:
        log_message("ERROR: Failed to set IP address", "ERROR")
        return False

    # Verify IP is set
    success, stdout, stderr = run_command(f"ip addr show {GUEST_INTERFACE}", "Verify wlan1 IP")
    if "192.168.4.1" not in stdout:
        log_message("ERROR: IP address not set correctly", "ERROR")
        return False

    log_message("wlan1 interface configured successfully")
    return True

def restart_services():
    """Restart all WiFi services in correct order"""
    log_message("=== RESTARTING SERVICES ===")

    # Stop services
    run_command("systemctl stop hostapd", "Stop hostapd")
    run_command("systemctl stop dnsmasq", "Stop dnsmasq")
    time.sleep(3)

    # Start dnsmasq first
    success, stdout, stderr = run_command("systemctl start dnsmasq", "Start dnsmasq")
    if not success:
        log_message("ERROR: Failed to start dnsmasq", "ERROR")
        run_command("journalctl -u dnsmasq -n 30", "Get dnsmasq error logs")
        return False

    time.sleep(2)

    # Start hostapd
    success, stdout, stderr = run_command("systemctl start hostapd", "Start hostapd")
    if not success:
        log_message("ERROR: Failed to start hostapd", "ERROR")
        run_command("journalctl -u hostapd -n 30", "Get hostapd error logs")
        return False

    time.sleep(3)

    # Verify services are running
    return check_services()

def test_wifi_broadcast():
    """Test if ValerieParty WiFi is broadcasting"""
    log_message("=== TESTING WIFI BROADCAST ===")

    # Check iwconfig
    success, stdout, stderr = run_command("iwconfig wlan1", "Check wlan1 mode")
    if "Mode:Master" not in stdout or "ValerieParty" not in stdout:
        log_message("ERROR: wlan1 not in Master mode or wrong ESSID", "ERROR")
        return False

    # Scan for the network
    success, stdout, stderr = run_command("iwlist scan | grep -A5 -B5 ValerieParty", "Scan for ValerieParty network", ignore_errors=True)
    if "ValerieParty" not in stdout:
        log_message("ERROR: ValerieParty network not visible in scan", "ERROR")
        return False

    log_message("ValerieParty WiFi is broadcasting correctly")
    return True

def test_flask_app():
    """Test if Flask app is reachable"""
    log_message("=== TESTING FLASK APP ===")

    # Test basic connectivity
    success, stdout, stderr = run_command(f"curl -m 10 http://{GUEST_IP}:5001/", "Test Flask app root", ignore_errors=True)
    if not success:
        log_message("ERROR: Cannot reach Flask app", "ERROR")
        return False

    # Test mobile endpoint
    success, stdout, stderr = run_command(f"curl -m 10 http://{GUEST_IP}:5001/mobile/", "Test Flask mobile endpoint", ignore_errors=True)
    if not success:
        log_message("ERROR: Cannot reach mobile endpoint", "ERROR")
        return False

    log_message("Flask app is responding correctly")
    return True

def full_diagnostic():
    """Run complete diagnostic"""
    log_message("=== RUNNING COMPLETE DIAGNOSTIC ===")

    # Check processes
    run_command("ps aux | grep hostapd", "Check hostapd processes")
    run_command("ps aux | grep dnsmasq", "Check dnsmasq processes")
    run_command("ps aux | grep python", "Check Python processes")

    # Check network configuration files
    run_command("cat /etc/hostapd/hostapd.conf", "Check hostapd config")
    run_command("grep -A5 'interface=wlan1' /etc/dnsmasq.conf", "Check dnsmasq config")

    # Check system resources
    run_command("free -h", "Check memory usage")
    run_command("df -h", "Check disk usage")

    # Check recent logs
    run_command("journalctl -u hostapd -n 50", "Recent hostapd logs")
    run_command("journalctl -u dnsmasq -n 50", "Recent dnsmasq logs")

def main():
    """Main repair function"""
    # Clear log file
    with open(LOG_FILE, "w") as f:
        f.write(f"ValerieParty WiFi Debug & Fix Log - {datetime.datetime.now()}\n")
        f.write("="*60 + "\n")

    log_message("Starting ValerieParty WiFi debug and fix")

    # Run full diagnostic first
    full_diagnostic()

    # Step 1: Check system status
    log_message("STEP 1: Checking system status")
    if not check_system_status():
        log_message("System status check failed, attempting to fix wlan1")
        if not fix_wlan1_interface():
            log_message("CRITICAL: Cannot fix wlan1 interface", "ERROR")
            return False

    # Step 2: Check and restart services
    log_message("STEP 2: Checking services")
    if not check_services():
        log_message("Services not running properly, restarting...")
        if not restart_services():
            log_message("CRITICAL: Cannot restart services", "ERROR")
            return False

    # Step 3: Test WiFi broadcast
    log_message("STEP 3: Testing WiFi broadcast")
    if not test_wifi_broadcast():
        log_message("WiFi broadcast failed, attempting service restart")
        if not restart_services():
            log_message("CRITICAL: Cannot fix WiFi broadcast", "ERROR")
            return False
        # Test again
        if not test_wifi_broadcast():
            log_message("CRITICAL: WiFi broadcast still failing", "ERROR")
            return False

    # Step 4: Test Flask app
    log_message("STEP 4: Testing Flask app")
    if not test_flask_app():
        log_message("WARNING: Flask app not responding, check if app is running", "WARNING")

    log_message("SUCCESS: ValerieParty WiFi setup completed successfully!", "SUCCESS")
    log_message("Guests should now be able to:")
    log_message("1. See 'ValerieParty' WiFi network")
    log_message("2. Connect to it")
    log_message("3. Access http://192.168.4.1:5001/mobile/")

    log_message(f"Complete log saved to: {LOG_FILE}")
    print(f"\nDEBUG COMPLETED. Check {LOG_FILE} for full details.")
    return True

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("ERROR: This script must be run with sudo")
        print("Usage: sudo python debug_fix_wifi.py")
        sys.exit(1)

    success = main()
    sys.exit(0 if success else 1)