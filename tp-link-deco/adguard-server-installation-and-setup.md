# Installation and Setup Guide: TPLink Router Host Generation for AdGuard

## Overview

`generate_hosts.py` logs into a TP-Link Deco router, reads the list of client devices, and writes them into `/etc/hosts` so AdGuard Home can resolve local devices by name.

### Offline devices are preserved

The Deco API only reports clients that are **currently connected**. Earlier versions of the script rebuilt the device list from scratch on every run, so any device that was asleep or disconnected at run time (phones, laptops, IoT devices on power-saving schedules) disappeared from `/etc/hosts` until the next run that happened to catch it online.

The script now merges the router's current client list with the entries already in the `# --- BEGIN/END TPLink Device List ---` section of the existing hosts file:

| Situation | Result |
|---|---|
| Device is connected | Written with its current IP (no comment) |
| Device was seen before but is not connected now | Kept, with a `# last seen: YYYY-MM-DD HH:MM:SS` comment |
| Known device reconnects with a new IP | Entry is updated to the new IP |
| An offline entry's IP is now used by a connected device | Offline entry is removed (the connected device wins) |
| Several offline entries share the same IP | Only the most recently seen one is kept |

Entries are sorted by IP address. Example output:

```
# --- BEGIN TPLink Device List ---
10.1.0.200  adguard adguard.home
10.1.0.12	living-room-tv
10.1.0.34	pixel-8  # last seen: 2026-11-06 22:00:01
10.1.0.57	macbook-pro
# --- END TPLink Device List ---
```

Offline entries do not expire on their own. To remove a device you no longer own, delete its line from `/etc/hosts`. It will not come back unless the device reconnects.

> **Note:** Every run regenerates the whole hosts file, including the localhost header. Any manual entries you add outside the TPLink section are overwritten.

### Additional safety checks

- **Hostname sanitizing:** hostnames are lowercased, and every character other than `a-z`, `0-9`, `.` and `-` becomes a hyphen. Repeated hyphens are collapsed, leading and trailing hyphens and dots are stripped, and names are capped at 253 characters. Devices without a usable hostname are skipped.
- **IP validation:** devices with an invalid IP address are skipped.
- **Router URL validation:** `TPLINK_GATEWAY` must be a private-range IP address.
- **Root check:** when the script writes to `/etc/hosts`, it refuses to run unless it runs as root.
- **Atomic writes:** the new hosts file is written to a temp file and then renamed into place, so a crash or error partway through never leaves `/etc/hosts` half-written.
- **Run summary:** each run logs how many devices were new, updated, kept offline, removed because of an IP conflict or a duplicate IP, and skipped.

## Prerequisites
- Debian 12 server with AdGuard installed
- Root or sudo access
- TPLink router password

## 1. Install Required Packages
```bash
# Update package lists
sudo apt update
# Install Python 3.11 and pip if not already installed
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
```

## 2. Install the TPLink Router Package
```bash
# Install the package using pip
sudo pip3 install tplinkrouterc6u
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
set -a
source /opt/TPLink/tplink.env
set +a

# Run the Python script and log output
/usr/bin/python3 /opt/TPLink/generate_hosts.py 2>&1
```

Set permissions for the wrapper script:
```bash
sudo chmod 755 /opt/TPLink/run_generate_hosts.sh
```

## 6. Create Cron Job
```bash
# Edit root's crontab
sudo crontab -e
```

Add the following line:
```
0 * * * * /opt/TPLink/run_generate_hosts.sh
```

## 7. Test the Setup

### Dry run (optional)

Set `TESTING=1` to run the script without root and without touching `/etc/hosts`. The output goes to `./hosts.test` and the log goes to `./testing.log`, both in the current directory. Run it more than once to watch offline devices being kept between runs.

```bash
cd /tmp
sudo bash -c 'set -a; source /opt/TPLink/tplink.env; set +a; TESTING=1 python3 /opt/TPLink/generate_hosts.py'
cat ./hosts.test
```

### Live run

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
   - `Root access required`: run the script as root (for example, from root's crontab) or use `TESTING=1`
   - `Invalid router URL`: `TPLINK_GATEWAY` must be a bare private IP such as `10.1.0.1`, with no `http://` prefix

2. If a device is missing or stale:
   - Search the log for its name. Each run logs new and updated devices, IP conflicts, and removed duplicates
   - A stale offline entry can be deleted from `/etc/hosts` by hand


3. If AdGuard isn't picking up changes:
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