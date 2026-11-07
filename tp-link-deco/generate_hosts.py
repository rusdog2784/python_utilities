import logging
import os
import sys
import re
import ipaddress
import tempfile

from datetime import datetime
from logging.handlers import RotatingFileHandler
from tplinkrouterc6u import TPLinkDecoClient


TESTING = int(os.getenv("TESTING", 0))
if TESTING == 1:
    TESTING = True
    print(f"TESTING MODE ENABLED")
else:
    TESTING = False


def setup_logger(log_file="/var/log/TPLink/generate_hosts.log"):
    """Set up a rotating logger
    
    Args:
        log_file (str): Path to log file
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('TPLinkHostsGenerator')
    logger.setLevel(logging.INFO)
    
    # Create rotating file handler (10 MB max file size, keep 5 backup files)
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add formatter to handler
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


def sanitize_hostname(hostname):
    """
    Sanitize hostname to prevent injection attacks and ensure valid format.
    
    Args:
        hostname (str): Raw hostname from device
        
    Returns:
        str: Sanitized hostname safe for hosts file
    """
    if not hostname:
        return None
    
    # Convert to lowercase and strip whitespace
    hostname = hostname.lower().strip()
    
    # Replace spaces and invalid characters with hyphens
    # Only allow: alphanumeric, hyphens, and dots
    hostname = re.sub(r'[^a-z0-9.-]', '-', hostname)
    
    # Remove consecutive hyphens
    hostname = re.sub(r'-+', '-', hostname)
    
    # Remove leading/trailing hyphens and dots
    hostname = hostname.strip('-.')
    
    # Ensure hostname doesn't exceed 253 characters (DNS limit)
    hostname = hostname[:253]
    
    # Validate final hostname is not empty and doesn't start with a digit
    if not hostname or len(hostname) < 1:
        return None
    
    return hostname


def is_valid_ip(ip_str):
    """
    Validate IP address format.
    
    Args:
        ip_str (str): IP address string
        
    Returns:
        bool: True if valid IP address
    """
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def validate_router_url(url):
    """
    Basic validation for router URL.
    
    Args:
        url (str): Router URL
        
    Returns:
        bool: True if URL format is acceptable
    """
    # Only allow http/https with local network IPs
    if not url.startswith(('http://', 'https://')):
        return False
    
    # Extract IP from URL
    try:
        ip_part = url.replace('http://', '').replace('https://', '').split(':')[0]
        ip = ipaddress.ip_address(ip_part)
        # Only allow private network IPs
        return ip.is_private
    except ValueError:
        return False


def atomic_write(content, filepath):
    """
    Write file atomically to prevent corruption.
    
    Args:
        content (str): Content to write
        filepath (str): Destination file path
    """
    # Create temp file in same directory as target
    dir_name = os.path.dirname(filepath) or '.'
    temp_fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix='.hosts_tmp_')
    
    try:
        # Write to temp file
        with os.fdopen(temp_fd, 'w') as f:
            f.write(content)
        
        # Set same permissions as original hosts file (644)
        os.chmod(temp_path, 0o644)
        
        # Atomic rename
        os.replace(temp_path, filepath)
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def parse_existing_hosts(filepath):
    """
    Parse existing hosts file and extract TPLink device entries.
    
    Args:
        filepath (str): Path to hosts file
        
    Returns:
        dict: Dictionary mapping hostnames to (ip, last_seen, comment)
    """
    existing_devices = {}
    
    try:
        with open(filepath, 'r') as f:
            in_tplink_section = False
            
            for line in f:
                line = line.strip()
                
                # Check for TPLink section markers
                if '# --- BEGIN TPLink Device List ---' in line:
                    in_tplink_section = True
                    continue
                elif '# --- END TPLink Device List ---' in line:
                    in_tplink_section = False
                    continue
                
                # Parse entries in TPLink section
                if in_tplink_section and line and not line.startswith('#'):
                    # Skip the hardcoded adguard entry
                    if 'adguard' in line:
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 2:
                        ip = parts[0]
                        hostname = parts[1]
                        
                        # Check if there's a "last seen" comment
                        last_seen = None
                        comment = None
                        if '#' in line:
                            comment_part = line.split('#', 1)[1].strip()
                            if 'last seen:' in comment_part:
                                try:
                                    last_seen = comment_part.split('last seen:', 1)[1].strip()
                                except:
                                    pass
                        
                        if is_valid_ip(ip):
                            existing_devices[hostname] = {
                                'ip': ip,
                                'last_seen': last_seen,
                                'comment': comment
                            }
    except FileNotFoundError:
        # If file doesn't exist, return empty dict
        pass
    except Exception as e:
        # Log but don't fail - we can still create a new file
        print(f"Warning: Could not parse existing hosts file: {e}")
    
    return existing_devices


def generate_hosts_file(router_url, password, output_file="/etc/hosts"):
    """
    Connect to TPLink router, get device information, and generate a hosts file.
    Merges with existing entries to preserve offline devices.
    
    Args:
        router_url (str): URL of the router (e.g., "http://10.1.0.1")
        password (str): Router password
        output_file (str): Path to output hosts file
    """
    # Set up logger
    logger = setup_logger(log_file="./testing.log") if TESTING else setup_logger()
    logger.info(f"Starting hosts file generation at {datetime.now()}")
    
    # Validate router URL
    if not validate_router_url(router_url):
        logger.error("Invalid router URL format or non-private IP address")
        raise ValueError("Invalid router URL")
    
    # Check if running with appropriate permissions for /etc/hosts
    if not TESTING and output_file == "/etc/hosts":
        if os.geteuid() != 0:
            logger.error("Script must be run as root to modify /etc/hosts")
            raise PermissionError("Root access required")
    
    # Parse existing hosts file to preserve offline devices
    logger.info("Parsing existing hosts file")
    existing_devices = parse_existing_hosts(output_file)
    logger.info(f"Found {len(existing_devices)} existing TPLink device entries")
    
    router = None
    try:
        # Connect to router and get device information
        logger.info("Attempting to connect to router")
        router = TPLinkDecoClient(router_url, password)
        router.authorize()
        logger.info("Successfully connected to router")
        
        try:
            status = router.get_status()
            logger.info(f"Retrieved status for {len(status.devices)} currently connected devices")
            
            # Standard hosts file header
            hosts_content = [
                "# /etc/hosts file generated from TPLink router data",
                f"# Generated by generate_hosts.py script at {datetime.now()}",
                "",
                "# localhost entries",
                "127.0.0.1   localhost",
                "::1         localhost ip6-localhost ip6-loopback",
                "ff02::1     ip6-allnodes",
                "ff02::2     ip6-allrouters",
                "",
                "# --- BEGIN TPLink Device List ---",
                "10.1.0.200  adguard adguard.home",
            ]
            
            # Track currently connected devices and their IPs
            current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            currently_connected = {}
            active_ips = set()
            devices_added = 0
            devices_updated = 0
            devices_skipped = 0
            
            # Process currently connected devices
            for device in status.devices:
                # Skip AdGuard device
                if device.ipaddr == "10.1.0.200":
                    continue
                
                # Validate IP address
                if not is_valid_ip(device.ipaddr):
                    logger.warning(f"Invalid IP address: {device.ipaddr}, skipping")
                    devices_skipped += 1
                    continue
                
                # Sanitize hostname
                hostname = sanitize_hostname(device.hostname)
                if not hostname:
                    logger.warning(f"Invalid hostname for device {device.ipaddr}, skipping")
                    devices_skipped += 1
                    continue
                
                # Track this device as currently connected
                currently_connected[hostname] = {
                    'ip': device.ipaddr,
                    'last_seen': current_timestamp,
                    'online': True
                }
                active_ips.add(device.ipaddr)
                
                # Check if this is a new device or updated device
                if hostname in existing_devices:
                    if existing_devices[hostname]['ip'] != device.ipaddr:
                        logger.info(f"Updated device: {hostname} ({existing_devices[hostname]['ip']} -> {device.ipaddr})")
                        devices_updated += 1
                    else:
                        logger.debug(f"Device still connected: {hostname} ({device.ipaddr})")
                else:
                    logger.info(f"New device discovered: {hostname} ({device.ipaddr})")
                    devices_added += 1
            
            # Merge currently connected devices with existing offline devices
            all_devices = {}
            
            # Add currently connected devices first
            for hostname, info in currently_connected.items():
                all_devices[hostname] = info
            
            # Add previously seen devices that are currently offline
            # BUT skip them if their IP is now used by an active device
            # First, collect all offline devices and group by IP to handle duplicates
            offline_devices_by_ip = {}
            devices_preserved = 0
            devices_removed_conflict = 0
            devices_removed_duplicate = 0
            
            for hostname, info in existing_devices.items():
                if hostname not in currently_connected:
                    # Check if this offline device's IP is now used by an online device
                    if info['ip'] in active_ips:
                        # IP conflict: online device takes precedence
                        logger.warning(f"IP conflict detected: {hostname} (offline) had IP {info['ip']}, "
                                     f"now assigned to an online device. Removing offline entry.")
                        devices_removed_conflict += 1
                    else:
                        # Device is offline, collect it for duplicate IP checking
                        device_ip = info['ip']
                        if device_ip not in offline_devices_by_ip:
                            offline_devices_by_ip[device_ip] = []
                        offline_devices_by_ip[device_ip].append({
                            'hostname': hostname,
                            'ip': info['ip'],
                            'last_seen': info['last_seen'] or current_timestamp,
                            'online': False
                        })
            
            # Process offline devices: if multiple devices share same IP, keep most recent
            for ip, devices_list in offline_devices_by_ip.items():
                if len(devices_list) == 1:
                    # No duplicate, just add it
                    device = devices_list[0]
                    all_devices[device['hostname']] = device
                    devices_preserved += 1
                    logger.debug(f"Preserving offline device: {device['hostname']} ({device['ip']})")
                else:
                    # Multiple offline devices with same IP - keep most recent
                    # Sort by last_seen timestamp (most recent first)
                    devices_list.sort(key=lambda d: d['last_seen'], reverse=True)
                    most_recent = devices_list[0]
                    
                    # Add the most recent one
                    all_devices[most_recent['hostname']] = most_recent
                    devices_preserved += 1
                    logger.info(f"Preserving most recent offline device for IP {ip}: {most_recent['hostname']} "
                               f"(last seen: {most_recent['last_seen']})")
                    
                    # Log the removed duplicates
                    for old_device in devices_list[1:]:
                        logger.info(f"Removing older duplicate for IP {ip}: {old_device['hostname']} "
                                   f"(last seen: {old_device['last_seen']})")
                        devices_removed_duplicate += 1
            
            # Sort devices by IP address for consistent ordering
            sorted_devices = sorted(all_devices.items(), key=lambda x: ipaddress.ip_address(x[1]['ip']))
            
            # Add all devices to hosts file
            for hostname, info in sorted_devices:
                if info.get('online', False):
                    # Currently online device
                    hosts_content.append(f"{info['ip']}\t{hostname}")
                else:
                    # Offline device - add comment with last seen timestamp
                    hosts_content.append(f"{info['ip']}\t{hostname}  # last seen: {info['last_seen']}")
            
            # Add footer
            hosts_content.append("# --- END TPLink Device List ---")
            hosts_content.append("")
            
            logger.info(f"Summary: {devices_added} new, {devices_updated} updated, "
                       f"{devices_preserved} preserved offline, {devices_removed_conflict} removed (IP conflict), "
                       f"{devices_removed_duplicate} removed (duplicate IP), {devices_skipped} skipped, "
                       f"{len(all_devices)} total entries")
            
            # Write to file atomically
            logger.info(f"Writing hosts file to {output_file}")
            hosts_file_content = '\n'.join(hosts_content)
            atomic_write(hosts_file_content, output_file)
            
            logger.info("Hosts file generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating hosts file: {str(e)}")
            raise
    except Exception as e:
        logger.error(f"Error connecting to router: {str(e)}")
        raise
    finally:
        # Ensure we always logout
        if router:
            try:
                router.logout()
                logger.info(f"Successfully logged out from router at {datetime.now()}")
            except Exception as e:
                logger.error(f"Error during logout: {str(e)}")


if __name__ == "__main__":
    # Get router configuration from environment variables
    router_gateway = os.getenv("TPLINK_GATEWAY")
    router_password = os.getenv("TPLINK_PASSWORD")
    
    if not router_password or not router_gateway:
        print("Error: TPLINK_GATEWAY and TPLINK_PASSWORD environment variables must be set", file=sys.stderr)
        sys.exit(1)
    
    # Validate gateway format
    if not router_gateway.replace('.', '').isdigit():
        print("Error: TPLINK_GATEWAY must be a valid IP address", file=sys.stderr)
        sys.exit(1)
    
    try:
        if TESTING:
            generate_hosts_file(f"http://{router_gateway}", router_password, output_file="./hosts.test")
        else:
            generate_hosts_file(f"http://{router_gateway}", router_password)
    except Exception as e:
        # Main exception handler for clean exit
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
