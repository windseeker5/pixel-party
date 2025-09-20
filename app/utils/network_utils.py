"""Network utilities for getting IP addresses."""

import socket
import subprocess
import platform

def get_network_ip(prefer_interface=None):
    """
    Get the network IP address of the machine.
    Returns the IP address that other devices on the network can use to connect.

    Args:
        prefer_interface: Preferred network interface name (e.g., 'wlan1')
    """
    try:
        # PRIORITY: Check for ValerieParty AP (wlan1) first
        # This is the guest network for the party
        try:
            result = subprocess.run(['ip', 'addr', 'show', 'wlan1'],
                                  capture_output=True, text=True, timeout=1)
            if result.returncode == 0 and '192.168.4.1' in result.stdout:
                return '192.168.4.1'  # Return wlan1 IP for party network
        except:
            pass
        # Method 1: Try using netifaces if available
        try:
            import netifaces
            interfaces = netifaces.interfaces()
            
            for iface in interfaces:
                # Skip loopback interface
                if iface == 'lo':
                    continue
                    
                addrs = netifaces.ifaddresses(iface)
                
                # Get IPv4 addresses
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        # Skip localhost and link-local addresses
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            return ip
        except ImportError:
            pass  # netifaces not available, try other methods
        
        # Method 2: Use socket connection to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        try:
            # Connect to Google's DNS server (doesn't actually send data)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            if not ip.startswith('127.'):
                return ip
        except:
            s.close()
        
        # Method 3: Try system commands based on OS
        system = platform.system()
        
        if system == "Linux":
            # Try ip command first (modern Linux)
            try:
                result = subprocess.run(['ip', 'route', 'get', '1'], 
                                      capture_output=True, text=True, timeout=1)
                if result.returncode == 0:
                    # Parse output like: "1.0.0.0 via 192.168.1.1 dev wlan0 src 192.168.1.89 uid 1000"
                    parts = result.stdout.split()
                    if 'src' in parts:
                        src_index = parts.index('src')
                        if src_index + 1 < len(parts):
                            ip = parts[src_index + 1]
                            if not ip.startswith('127.'):
                                return ip
            except:
                pass
            
            # Try hostname command as fallback
            try:
                result = subprocess.run(['hostname', '-I'], 
                                      capture_output=True, text=True, timeout=1)
                if result.returncode == 0:
                    ips = result.stdout.strip().split()
                    for ip in ips:
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            return ip
            except:
                pass
                
        elif system == "Darwin":  # macOS
            try:
                result = subprocess.run(['ipconfig', 'getifaddr', 'en0'], 
                                      capture_output=True, text=True, timeout=1)
                if result.returncode == 0:
                    ip = result.stdout.strip()
                    if ip and not ip.startswith('127.'):
                        return ip
            except:
                pass
        
        elif system == "Windows":
            try:
                result = subprocess.run(['ipconfig'], 
                                      capture_output=True, text=True, timeout=1)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for i, line in enumerate(lines):
                        if 'IPv4' in line and i + 1 < len(lines):
                            ip = lines[i].split(':')[-1].strip()
                            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                                return ip
            except:
                pass
            
    except Exception as e:
        print(f"Warning: Could not determine network IP: {e}")
    
    # Fallback to localhost if we can't determine network IP
    return '127.0.0.1'

def get_server_url(port=5000):
    """
    Get the full server URL that can be accessed from other devices on the network.
    
    Args:
        port: The port number the server is running on
        
    Returns:
        The full URL (e.g., http://192.168.1.89:5000)
    """
    ip = get_network_ip()
    return f"http://{ip}:{port}"