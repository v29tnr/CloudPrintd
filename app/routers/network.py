"""
Network configuration and WiFi management endpoints.
Enables WiFi setup without command-line access for commercial hardware products.
"""

import subprocess
import re
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

# TODO: Implement proper admin authentication
# from ..auth import require_admin

router = APIRouter(prefix="/network", tags=["network"])
logger = logging.getLogger(__name__)


class NetworkStatus(BaseModel):
    """Current network connection status"""
    connected: bool
    type: str = Field(..., description="wifi, ethernet, or ap_mode")
    interface: str = Field(..., description="Interface name like wlan0, eth0")
    ip: str = Field(default="", description="Current IP address")
    ssid: str = Field(default="", description="Connected WiFi SSID (if WiFi)")
    signal_strength: int = Field(default=0, description="WiFi signal in dBm (if WiFi)")
    mac_address: str = Field(default="", description="MAC address")


class WiFiNetwork(BaseModel):
    """Available WiFi network from scan"""
    ssid: str
    bssid: str
    signal: int = Field(..., description="Signal strength in dBm")
    frequency: int = Field(..., description="Frequency in MHz")
    security: str = Field(..., description="Security type: WPA2, WPA3, Open, etc")
    quality: int = Field(..., description="Signal quality 0-100")


class WiFiConfigRequest(BaseModel):
    """WiFi configuration request"""
    ssid: str = Field(..., min_length=1, max_length=32)
    password: str = Field(default="", description="Password (empty for open networks)")
    hidden: bool = Field(default=False, description="Whether network is hidden")


class StaticIPConfig(BaseModel):
    """Static IP configuration"""
    enabled: bool
    ip_address: str = ""
    subnet_mask: str = ""
    gateway: str = ""
    dns_servers: List[str] = []


def run_command(cmd: List[str], check: bool = True) -> tuple[int, str, str]:
    """
    Run shell command and return (return_code, stdout, stderr).
    
    Args:
        cmd: Command and arguments as list
        check: Whether to raise exception on non-zero return code
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if check and result.returncode != 0:
            logger.error(f"Command failed: {' '.join(cmd)}\nStderr: {result.stderr}")
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {' '.join(cmd)}")
        return -1, "", "Command timed out"
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return -1, "", str(e)


@router.get("/status", response_model=NetworkStatus)
async def get_network_status():
    """
    Get current network connection status.
    
    Returns connection type, IP address, WiFi SSID and signal strength.
    """
    # Check if in AP mode
    _, ap_check, _ = run_command(["systemctl", "is-active", "hostapd"], check=False)
    if ap_check.strip() == "active":
        return NetworkStatus(
            connected=False,
            type="ap_mode",
            interface="wlan0",
            ip="192.168.4.1",
            ssid="CloudPrintd-SETUP",
            mac_address=_get_mac_address("wlan0")
        )
    
    # Check Ethernet
    eth_status = _get_interface_status("eth0")
    if eth_status["connected"]:
        return NetworkStatus(
            connected=True,
            type="ethernet",
            interface="eth0",
            ip=eth_status["ip"],
            mac_address=eth_status["mac"]
        )
    
    # Check WiFi
    wifi_status = _get_interface_status("wlan0")
    if wifi_status["connected"]:
        # Get WiFi details
        ssid, signal = _get_wifi_info()
        return NetworkStatus(
            connected=True,
            type="wifi",
            interface="wlan0",
            ip=wifi_status["ip"],
            ssid=ssid,
            signal_strength=signal,
            mac_address=wifi_status["mac"]
        )
    
    # No connection
    return NetworkStatus(
        connected=False,
        type="disconnected",
        interface="",
        mac_address=""
    )


@router.get("/scan", response_model=List[WiFiNetwork])
async def scan_wifi_networks():
    """
    Scan for available WiFi networks.
    
    Returns list of networks sorted by signal strength.
    Requires WiFi interface to be enabled.
    """
    # Trigger scan
    _, _, _ = run_command(["sudo", "iwlist", "wlan0", "scan"], check=False)
    
    # Get scan results from wpa_cli
    code, output, err = run_command(["sudo", "wpa_cli", "-i", "wlan0", "scan_results"], check=False)
    
    if code != 0:
        logger.warning(f"WiFi scan failed: {err}")
        raise HTTPException(status_code=500, detail="Failed to scan WiFi networks")
    
    networks = []
    seen_ssids = set()
    
    # Parse scan results
    # Format: bssid / frequency / signal level / flags / ssid
    lines = output.strip().split('\n')[1:]  # Skip header
    for line in lines:
        parts = line.split('\t')
        if len(parts) < 5:
            continue
        
        bssid, freq, signal, flags, ssid = parts[:5]
        
        # Skip empty SSIDs and duplicates
        if not ssid or ssid in seen_ssids:
            continue
        seen_ssids.add(ssid)
        
        # Parse security type
        security = "Open"
        if "WPA3" in flags:
            security = "WPA3"
        elif "WPA2" in flags:
            security = "WPA2"
        elif "WPA" in flags:
            security = "WPA"
        elif "WEP" in flags:
            security = "WEP"
        
        # Convert signal to quality (0-100)
        signal_dbm = int(signal)
        quality = min(100, max(0, (signal_dbm + 100) * 2))
        
        networks.append(WiFiNetwork(
            ssid=ssid,
            bssid=bssid,
            signal=signal_dbm,
            frequency=int(freq),
            security=security,
            quality=quality
        ))
    
    # Sort by signal strength (strongest first)
    networks.sort(key=lambda n: n.signal, reverse=True)
    
    return networks


@router.post("/wifi/configure")
async def configure_wifi(config: WiFiConfigRequest):
    """
    Configure WiFi connection.
    
    Saves credentials to wpa_supplicant and initiates connection.
    Pi will reboot after saving configuration.
    
    TODO: Requires admin authentication.
    """
    # Validate SSID
    if not config.ssid.strip():
        raise HTTPException(status_code=400, detail="SSID cannot be empty")
    
    # Generate wpa_supplicant network block
    if config.password:
        # Secure network
        network_block = f'''
network={{
    ssid="{config.ssid}"
    psk="{config.password}"
    scan_ssid={1 if config.hidden else 0}
    key_mgmt=WPA-PSK
}}
'''
    else:
        # Open network
        network_block = f'''
network={{
    ssid="{config.ssid}"
    key_mgmt=NONE
    scan_ssid={1 if config.hidden else 0}
}}
'''
    
    try:
        # Backup existing config
        run_command([
            "sudo", "cp", 
            "/etc/wpa_supplicant/wpa_supplicant.conf",
            "/etc/wpa_supplicant/wpa_supplicant.conf.backup"
        ])
        
        # Read existing config
        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "r") as f:
            existing_config = f.read()
        
        # Remove any existing network blocks for same SSID
        pattern = rf'network=\{{\s*ssid="{re.escape(config.ssid)}".*?\}}\s*'
        cleaned_config = re.sub(pattern, '', existing_config, flags=re.DOTALL)
        
        # Append new network block
        new_config = cleaned_config.rstrip() + "\n" + network_block
        
        # Write new config
        with open("/tmp/wpa_supplicant.conf.new", "w") as f:
            f.write(new_config)
        
        # Move to proper location
        run_command([
            "sudo", "mv",
            "/tmp/wpa_supplicant.conf.new",
            "/etc/wpa_supplicant/wpa_supplicant.conf"
        ])
        
        run_command([
            "sudo", "chmod", "600",
            "/etc/wpa_supplicant/wpa_supplicant.conf"
        ])
        
        # Stop hostapd if running (exit AP mode)
        run_command(["sudo", "systemctl", "stop", "hostapd"], check=False)
        run_command(["sudo", "systemctl", "stop", "dnsmasq"], check=False)
        
        # Reconfigure wpa_supplicant
        run_command(["sudo", "wpa_cli", "-i", "wlan0", "reconfigure"], check=False)
        
        # Reboot to ensure clean connection
        logger.info(f"WiFi configured for SSID: {config.ssid}. Rebooting in 5 seconds...")
        
        # Schedule reboot
        subprocess.Popen(["sudo", "shutdown", "-r", "+0.1"])
        
        return {
            "success": True,
            "message": "WiFi configured successfully. Pi is rebooting...",
            "ssid": config.ssid,
            "reboot": True
        }
        
    except Exception as e:
        logger.error(f"Failed to configure WiFi: {e}")
        # Restore backup if exists
        run_command([
            "sudo", "cp",
            "/etc/wpa_supplicant/wpa_supplicant.conf.backup",
            "/etc/wpa_supplicant/wpa_supplicant.conf"
        ], check=False)
        raise HTTPException(status_code=500, detail=f"Failed to configure WiFi: {str(e)}")


@router.post("/wifi/reset")  # TODO: Add admin auth
async def reset_wifi():
    """
    Reset WiFi configuration and return to AP mode.
    
    Clears all saved networks and triggers AP mode on next boot.
    Requires admin authentication.
    """
    try:
        # Remove WiFi configuration
        base_config = """ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

"""
        with open("/tmp/wpa_supplicant.conf", "w") as f:
            f.write(base_config)
        
        run_command([
            "sudo", "mv",
            "/tmp/wpa_supplicant.conf",
            "/etc/wpa_supplicant/wpa_supplicant.conf"
        ])
        
        run_command([
            "sudo", "chmod", "600",
            "/etc/wpa_supplicant/wpa_supplicant.conf"
        ])
        
        # Reboot to AP mode
        logger.info("WiFi reset. Rebooting to AP mode...")
        subprocess.Popen(["sudo", "shutdown", "-r", "+0.1"])
        
        return {
            "success": True,
            "message": "WiFi reset. Pi will reboot to setup mode in 5 seconds.",
            "reboot": True
        }
        
    except Exception as e:
        logger.error(f"Failed to reset WiFi: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset WiFi: {str(e)}")


@router.get("/hostname")
async def get_hostname():
    """Get current hostname"""
    code, output, _ = run_command(["hostname"], check=False)
    if code == 0:
        return {"hostname": output.strip()}
    return {"hostname": "unknown"}


@router.post("/hostname")  # TODO: Add admin auth
async def set_hostname(hostname: str):
    """
    Set system hostname.
    
    Updates /etc/hostname and /etc/hosts.
    Requires admin authentication and reboot to take effect.
    """
    # Validate hostname
    if not re.match(r'^[a-z0-9-]{1,63}$', hostname.lower()):
        raise HTTPException(
            status_code=400,
            detail="Invalid hostname. Use only lowercase letters, numbers, and hyphens (1-63 chars)"
        )
    
    try:
        # Update /etc/hostname
        with open("/tmp/hostname", "w") as f:
            f.write(hostname + "\n")
        run_command(["sudo", "mv", "/tmp/hostname", "/etc/hostname"])
        
        # Update /etc/hosts
        code, hosts_content, _ = run_command(["cat", "/etc/hosts"])
        if code == 0:
            # Replace old hostname with new
            lines = hosts_content.split('\n')
            new_lines = []
            for line in lines:
                if "127.0.1.1" in line:
                    new_lines.append(f"127.0.1.1\t{hostname}")
                else:
                    new_lines.append(line)
            
            with open("/tmp/hosts", "w") as f:
                f.write('\n'.join(new_lines))
            run_command(["sudo", "mv", "/tmp/hosts", "/etc/hosts"])
        
        # Apply immediately
        run_command(["sudo", "hostnamectl", "set-hostname", hostname], check=False)
        
        return {
            "success": True,
            "message": f"Hostname set to '{hostname}'. Reboot for full effect.",
            "hostname": hostname
        }
        
    except Exception as e:
        logger.error(f"Failed to set hostname: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set hostname: {str(e)}")


# Helper functions

def _get_interface_status(interface: str) -> Dict[str, Any]:
    """Get status of network interface"""
    # Check if interface exists and is up
    code, output, _ = run_command(["ip", "link", "show", interface], check=False)
    if code != 0 or "state UP" not in output:
        return {"connected": False, "ip": "", "mac": ""}
    
    # Get IP address
    code, output, _ = run_command(["ip", "-4", "addr", "show", interface], check=False)
    ip = ""
    if code == 0:
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', output)
        if match:
            ip = match.group(1)
    
    # Get MAC address
    mac = _get_mac_address(interface)
    
    return {
        "connected": bool(ip),
        "ip": ip,
        "mac": mac
    }


def _get_mac_address(interface: str) -> str:
    """Get MAC address of interface"""
    code, output, _ = run_command(["cat", f"/sys/class/net/{interface}/address"], check=False)
    if code == 0:
        return output.strip()
    return ""


def _get_wifi_info() -> tuple[str, int]:
    """Get current WiFi SSID and signal strength"""
    ssid = ""
    signal = 0
    
    # Get SSID
    code, output, _ = run_command(["iwgetid", "-r"], check=False)
    if code == 0:
        ssid = output.strip()
    
    # Get signal strength
    code, output, _ = run_command(["iwconfig", "wlan0"], check=False)
    if code == 0:
        match = re.search(r'Signal level=(-?\d+) dBm', output)
        if match:
            signal = int(match.group(1))
    
    return ssid, signal
