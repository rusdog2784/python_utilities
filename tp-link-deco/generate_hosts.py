import logging
import os
import sys

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


def generate_hosts_file(router_url, password, output_file="/etc/hosts"):
    """
    Connect to TPLink router, get device information, and generate a hosts file.
    
    Args:
        router_url (str): URL of the router (e.g., "http://10.1.0.1")
        password (str): Router password
        output_file (str): Path to output hosts file
    """
    # Set up logger
    logger = setup_logger(log_file="./testing.log") if TESTING else setup_logger()
    logger.info(f"Starting hosts file generation at {datetime.now()}")
    
    try:
        # Connect to router and get device information
        logger.info(f"Attempting to connect to router at {router_url}")
        router = TPLinkDecoClient(router_url, password)
        router.authorize()
        logger.info("Successfully connected to router")
        
        try:
            status = router.get_status()
            logger.info(f"Retrieved status for {len(status.devices)} devices")
            
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
            
            # Add each device from the router
            for device in status.devices:
                # Create properly formatted hosts entry
                # Ensure hostname is lowercase and remove spaces/special chars
                if device.ipaddr == "10.1.0.200":
                    continue
                else:
                    hostname = device.hostname.lower().replace(" ", "-").replace("'", "")
                    hosts_content.append(f"{device.ipaddr}\t{hostname}")
                    logger.info(f"Added device: {hostname} ({device.ipaddr})")
            
            # Add final newline
            hosts_content.append("# --- END TPLink Device List ---",)
            hosts_content.append("")
            
            # Write to file
            logger.info(f"Writing hosts file to {output_file}")
            with open(output_file, 'w') as f:
                f.write('\n'.join(hosts_content))
            
            logger.info("Hosts file generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating hosts file: {str(e)}")
            raise
    except Exception as e:
        logger.error(f"Error connecting to router: {str(e)}")
        raise
    finally:
        # Ensure we always logout
        try:
            router.logout()
            logger.info(f"Successfully logged out from router at {datetime.now()}")
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")


if __name__ == "__main__":
    # Get router password from environment variable
    router_gateway = os.getenv("TPLINK_GATEWAY")
    router_password = os.getenv("TPLINK_PASSWORD")
    if not router_password or not router_gateway:
        print("TPLINK_GATEWAY and TPLINK_PASSWORD environment variables must be set", file=sys.stderr)
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
