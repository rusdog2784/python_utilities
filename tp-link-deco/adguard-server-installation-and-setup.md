# Installation and Setup Guide: TPLink Router Host Generation for AdGuard

## Prerequisites
- Debian 12 server with AdGuard installed
- Root or sudo access
- TPLink router password

## 1. Install Required Packages
```bash
# Update package lists
sudo apt update

# Install Python 3.10 and pip if not already installed
sudo apt install -y python3.10 python3.10-venv python3.10-dev python3-pip
```

## 2. Install the TPLink Router Package
```bash
# Install the package using pip
sudo pip3 install tplinkrouterc6u python-dotenv
```

## 3. Create Script Directory and Files
```bash
# Create a directory for the script
sudo mkdir -p /opt/TPLink

# Create a directory for logs
sudo mkdir -p /var/log/TPLink

# Copy the script to the directory
sudo nano /opt/TPLink/generate_hosts.py
# Paste the script content (https://github.com/rusdog2784/python_utilities/blob/main/tp-link-deco/generate_hosts.py)
# here and save (Ctrl+X, Y, Enter)

# Create environment file for the password
sudo nano /opt/TPLink/tplink.env
# Add the following lines (replace with your actual values):
# TPLINK_GATEWAY=your_router_gateway_ip_address
# TPLINK_PASSWORD=your_router_password
```

## 4. Set Proper Permissions
```bash
# Set ownership
sudo chown -R root:root /opt/TPLink

# Set proper permissions for the script and directories
sudo chmod 755 /opt/TPLink
sudo chmod 644 /opt/TPLink/generate_hosts.py
sudo chmod 600 /opt/TPLink/tplink.env
```

## 5. Create Wrapper Script
```bash
# Create a wrapper script that sources the environment file
sudo nano /opt/TPLink/run_generate_hosts.sh
```

Add the following content:
```bash
#!/bin/bash

# Source the environment file
source /opt/TPLink/tplink.env

# Run the Python script and log output
/usr/bin/python3 /opt/TPLink/generate_hosts.py 2>&1
```

Set permissions for the wrapper script:
```bash
sudo chmod 755 /opt/TPLink/run_generate_hosts.sh
```

## 7. Create Cron Job
```bash
# Edit root's crontab
sudo crontab -e
```

Add the following line:
```
0 * * * * /opt/TPLink/run_generate_hosts.sh
```

## 8. Test the Setup
```bash
# Run the script manually to test
sudo /opt/TPLink/run_generate_hosts.sh

# Check the log file
tail -f /var/log/TPLink/generate_hosts.log

# Verify the hosts file was created
cat /etc/hosts

# Check AdGuard status
systemctl status AdGuardHome
```

## Troubleshooting

1. If the script fails to run:
   - Check the log file: `tail -f /var/log/TPLink/generate_hosts.log`
   - Verify the password in tplink.env is correct
   - Ensure Python package is installed: `pip3 list | grep tplinkrouterc6u`

2. If AdGuard isn't picking up changes:
   - Verify AdGuard service name: `systemctl list-units | grep -i adguard`
   - Check AdGuard logs: `journalctl -u AdGuardHome`
   - Manually restart AdGuard: `systemctl restart AdGuardHome`

## Maintenance

- Monitor log file growth: `du -sh /var/log/TPLink/`
- Check script execution in syslog: `grep CRON /var/log/syslog`
- Periodically verify hosts file is being updated: `stat /etc/hosts`

## Security Notes

- The tplink.env file contains sensitive information and should remain chmod 600
- Regular monitoring of the log files is recommended
- Consider implementing file integrity monitoring for the script files