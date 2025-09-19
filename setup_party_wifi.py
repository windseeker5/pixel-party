#!/usr/bin/env python3
"""
ValerieParty WiFi Setup Script
Creates internet-enabled guest WiFi with automatic app redirection
Logs EVERYTHING so Claude can debug remotely
"""

import subprocess
import sys
import os
import datetime
import time

# Configuration
LOG_FILE = "party_setup.log"
APP_PORT = "5001"
GUEST_INTERFACE = "wlan1"
INTERNET_INTERFACE = "wlan0"
GUEST_IP = "192.168.4.1"

def log_message(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {level}: {message}"
    print(log_entry)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

def run_command(command, description, ignore_errors=False):
    """Run command and log everything"""
    log_message(f"Running: {description}")
    log_message(f"Command: {command}")

    try:
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
            return False
        return True

    except subprocess.TimeoutExpired:
        log_message(f"ERROR: Command timed out: {command}", "ERROR")
        return False
    except Exception as e:
        log_message(f"ERROR: Exception running command: {e}", "ERROR")
        return False

def check_prerequisites():
    """Check if everything we need is available"""
    log_message("=== CHECKING PREREQUISITES ===")

    # Check if running as root
    if os.geteuid() != 0:
        log_message("ERROR: Script must be run with sudo", "ERROR")
        return False

    # Check WiFi interfaces
    success = run_command("iwconfig", "Check WiFi interfaces")
    if not success:
        log_message("ERROR: Cannot check WiFi interfaces", "ERROR")
        return False

    # Check if dnsmasq is installed
    success = run_command("which dnsmasq", "Check if dnsmasq is installed")
    if not success:
        log_message("ERROR: dnsmasq not found", "ERROR")
        return False

    # Check if hostapd is installed
    success = run_command("which hostapd", "Check if hostapd is installed")
    if not success:
        log_message("ERROR: hostapd not found", "ERROR")
        return False

    log_message("Prerequisites check passed")
    return True

def fix_dnsmasq_config():
    """Fix the dnsmasq configuration"""
    log_message("=== FIXING DNSMASQ CONFIGURATION ===")

    config_file = "/etc/dnsmasq.conf"
    backup_file = f"{config_file}.backup.{int(time.time())}"

    # Backup current config
    run_command(f"cp {config_file} {backup_file}", "Backup dnsmasq config")

    try:
        # Read current config
        with open(config_file, 'r') as f:
            lines = f.readlines()

        # Remove problematic lines and ensure correct config
        new_lines = []
        in_pixelparty_section = False

        for line in lines:
            # Skip bad address lines
            if "address=/#/192.168.4.1:" in line:
                log_message(f"Removing bad line: {line.strip()}")
                continue

            # Mark start of our section
            if "# PixelParty Guest Network" in line:
                in_pixelparty_section = True

            new_lines.append(line)

        # Ensure our configuration is present and correct
        pixelparty_config = [
            "\n# PixelParty Guest Network\n",
            f"interface={GUEST_INTERFACE}\n",
            "dhcp-range=192.168.4.2,192.168.4.254,255.255.255.0,24h\n",
            f"address=/#/{GUEST_IP}\n"
        ]

        # Check if our config exists
        config_exists = any("interface=wlan1" in line for line in new_lines)
        if not config_exists:
            log_message("Adding PixelParty configuration to dnsmasq")
            new_lines.extend(pixelparty_config)

        # Write new config
        with open(config_file, 'w') as f:
            f.writelines(new_lines)

        log_message("dnsmasq configuration updated")

        # Test the configuration
        success = run_command("dnsmasq --test", "Test dnsmasq configuration")
        if not success:
            log_message("ERROR: dnsmasq config test failed", "ERROR")
            # Restore backup
            run_command(f"cp {backup_file} {config_file}", "Restore backup config")
            return False

        log_message("dnsmasq configuration is valid")
        return True

    except Exception as e:
        log_message(f"ERROR: Failed to fix dnsmasq config: {e}", "ERROR")
        # Restore backup
        run_command(f"cp {backup_file} {config_file}", "Restore backup config")
        return False

def setup_internet_forwarding():
    """Set up internet forwarding from wlan0 to wlan1"""
    log_message("=== SETTING UP INTERNET FORWARDING ===")

    # Enable IP forwarding
    success = run_command("sysctl -w net.ipv4.ip_forward=1", "Enable IP forwarding")
    if not success:
        return False

    # Make IP forwarding permanent
    success = run_command(
        'grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf || echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf',
        "Make IP forwarding permanent"
    )

    # Clear existing iptables rules for our chains
    run_command("iptables -t nat -D POSTROUTING -o wlan0 -j MASQUERADE", "Clear old NAT rule", ignore_errors=True)
    run_command("iptables -D FORWARD -i wlan1 -o wlan0 -j ACCEPT", "Clear old forward rule 1", ignore_errors=True)
    run_command("iptables -D FORWARD -i wlan0 -o wlan1 -m state --state RELATED,ESTABLISHED -j ACCEPT", "Clear old forward rule 2", ignore_errors=True)

    # Set up NAT
    success = run_command(
        f"iptables -t nat -A POSTROUTING -o {INTERNET_INTERFACE} -j MASQUERADE",
        "Set up NAT masquerading"
    )
    if not success:
        return False

    # Set up forwarding rules
    success = run_command(
        f"iptables -A FORWARD -i {GUEST_INTERFACE} -o {INTERNET_INTERFACE} -j ACCEPT",
        "Set up forward rule (guest to internet)"
    )
    if not success:
        return False

    success = run_command(
        f"iptables -A FORWARD -i {INTERNET_INTERFACE} -o {GUEST_INTERFACE} -m state --state RELATED,ESTABLISHED -j ACCEPT",
        "Set up forward rule (internet to guest)"
    )
    if not success:
        return False

    # Save iptables rules
    success = run_command(
        "sh -c 'iptables-save > /etc/iptables.ipv4.nat'",
        "Save iptables rules"
    )

    # Set up iptables restore on boot
    restore_line = "iptables-restore < /etc/iptables.ipv4.nat"
    run_command(
        f'grep -q "{restore_line}" /etc/rc.local || sed -i "/^exit 0/i {restore_line}" /etc/rc.local',
        "Set up iptables restore on boot"
    )

    log_message("Internet forwarding setup completed")
    return True

def restart_services():
    """Restart all necessary services"""
    log_message("=== RESTARTING SERVICES ===")

    # Stop services first
    run_command("systemctl stop hostapd", "Stop hostapd")
    run_command("systemctl stop dnsmasq", "Stop dnsmasq")

    # Configure interfaces
    success = run_command(
        f"ip addr add {GUEST_IP}/24 dev {GUEST_INTERFACE}",
        "Set guest interface IP",
        ignore_errors=True
    )

    success = run_command(
        f"ip link set dev {GUEST_INTERFACE} up",
        "Bring guest interface up"
    )

    # Start services
    success = run_command("systemctl start dnsmasq", "Start dnsmasq")
    if not success:
        log_message("ERROR: Failed to start dnsmasq", "ERROR")
        run_command("journalctl -u dnsmasq -n 20", "Get dnsmasq logs")
        return False

    success = run_command("systemctl start hostapd", "Start hostapd")
    if not success:
        log_message("ERROR: Failed to start hostapd", "ERROR")
        run_command("journalctl -u hostapd -n 20", "Get hostapd logs")
        return False

    # Enable services for auto-start
    run_command("systemctl enable dnsmasq", "Enable dnsmasq auto-start")
    run_command("systemctl enable hostapd", "Enable hostapd auto-start")

    log_message("Services restarted successfully")
    return True

def test_setup():
    """Test the complete setup"""
    log_message("=== TESTING SETUP ===")

    # Check service status
    run_command("systemctl status dnsmasq", "Check dnsmasq status")
    run_command("systemctl status hostapd", "Check hostapd status")

    # Check network interfaces
    run_command("iwconfig", "Check WiFi interfaces")
    run_command("ip addr show", "Check IP addresses")

    # Check iptables rules
    run_command("iptables -t nat -L", "Check NAT rules")
    run_command("iptables -L FORWARD", "Check forward rules")

    # Check if ValerieParty is broadcasting
    run_command("iwlist scan | grep -A5 -B5 ValerieParty", "Check if ValerieParty is visible", ignore_errors=True)

    # Test DHCP range
    run_command("journalctl -u dnsmasq | grep 'DHCP, IP range'", "Check DHCP configuration")

    log_message("Setup testing completed")

def main():
    """Main setup function"""
    # Clear log file
    with open(LOG_FILE, "w") as f:
        f.write(f"ValerieParty WiFi Setup Log - {datetime.datetime.now()}\n")
        f.write("="*50 + "\n")

    log_message("Starting ValerieParty WiFi setup")
    log_message(f"App will be accessible at: http://{GUEST_IP}:{APP_PORT}/mobile")

    success = True

    # Run all setup steps
    if not check_prerequisites():
        success = False

    if success and not fix_dnsmasq_config():
        success = False

    if success and not setup_internet_forwarding():
        success = False

    if success and not restart_services():
        success = False

    # Always run tests to see current state
    test_setup()

    if success:
        log_message("SUCCESS: ValerieParty WiFi setup completed!", "SUCCESS")
        log_message(f"Guests can now:")
        log_message(f"1. Connect to 'ValerieParty' WiFi")
        log_message(f"2. Get internet access")
        log_message(f"3. Browse normally OR go to http://{GUEST_IP}:{APP_PORT}/mobile")
        log_message(f"4. All web requests will redirect to your Pi anyway")
    else:
        log_message("FAILED: Setup encountered errors. Check log above.", "ERROR")
        log_message(f"Send the file '{LOG_FILE}' to Claude for debugging.")

    log_message(f"Log saved to: {LOG_FILE}")
    print(f"\nSetup {'COMPLETED' if success else 'FAILED'}. Check {LOG_FILE} for details.")

if __name__ == "__main__":
    main()