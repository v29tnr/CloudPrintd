#!/bin/bash
#
# CloudPrintd WiFi Setup Check
# Runs on boot to determine if Pi should enter AP (setup) mode
#
# If no WiFi is configured, start hostapd (WiFi AP) and dnsmasq (DHCP/DNS)
# Otherwise, connect to configured network normally
#

set -e

WLAN_INTERFACE="wlan0"
AP_SSID_PREFIX="CloudPrintd-SETUP"
AP_PASSWORD="cloudprintd"
AP_IP="192.168.4.1"
WPA_CONF="/etc/wpa_supplicant/wpa_supplicant.conf"
HOSTAPD_CONF="/etc/hostapd/hostapd.conf"
DNSMASQ_CONF="/etc/dnsmasq.d/cloudprintd-ap.conf"
LOG_FILE="/var/log/cloudprintd-wifi-setup.log"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Generate random 4-character suffix for AP SSID
generate_ssid_suffix() {
    # Use MAC address last 4 hex digits for consistency
    MAC=$(cat /sys/class/net/$WLAN_INTERFACE/address | tr -d ':')
    echo "${MAC: -4}" | tr '[:lower:]' '[:upper:]'
}

# Check if WiFi network is configured
is_wifi_configured() {
    # Check if wpa_supplicant.conf has any network blocks with SSID
    if grep -q '^[[:space:]]*network[[:space:]]*=' "$WPA_CONF" 2>/dev/null; then
        # Found network block, check if it has an SSID
        if grep -A 10 '^[[:space:]]*network[[:space:]]*=' "$WPA_CONF" | grep -q '^[[:space:]]*ssid='; then
            return 0  # Configured
        fi
    fi
    return 1  # Not configured
}

# Setup hostapd configuration
setup_hostapd() {
    local suffix=$(generate_ssid_suffix)
    local ssid="${AP_SSID_PREFIX}-${suffix}"
    
    log "Creating hostapd configuration for SSID: $ssid"
    
    cat > "$HOSTAPD_CONF" << EOF
# CloudPrintd WiFi AP Configuration
interface=$WLAN_INTERFACE
driver=nl80211
ssid=$ssid
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$AP_PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

    chmod 600 "$HOSTAPD_CONF"
}

# Setup dnsmasq configuration
setup_dnsmasq() {
    log "Creating dnsmasq configuration"
    
    mkdir -p /etc/dnsmasq.d
    
    cat > "$DNSMASQ_CONF" << EOF
# CloudPrintd AP DHCP/DNS Configuration
interface=$WLAN_INTERFACE
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
dhcp-option=3,192.168.4.1
dhcp-option=6,192.168.4.1
server=8.8.8.8
log-queries
log-dhcp
listen-address=192.168.4.1

# Captive portal - redirect all DNS queries to our IP
address=/#/192.168.4.1
EOF
}

# Setup network interface for AP mode
setup_ap_interface() {
    log "Configuring $WLAN_INTERFACE for AP mode"
    
    # Stop wpa_supplicant if running
    systemctl stop wpa_supplicant.service 2>/dev/null || true
    
    # Configure static IP for AP
    ip addr flush dev $WLAN_INTERFACE
    ip addr add $AP_IP/24 dev $WLAN_INTERFACE
    ip link set dev $WLAN_INTERFACE up
    
    log "Interface configured with IP: $AP_IP"
}

# Setup iptables for captive portal
setup_captive_portal() {
    log "Setting up captive portal redirect"
    
    # Clear existing rules
    iptables -t nat -F PREROUTING 2>/dev/null || true
    
    # Redirect HTTP to CloudPrintd web interface (port 8000)
    iptables -t nat -A PREROUTING -i $WLAN_INTERFACE -p tcp --dport 80 -j REDIRECT --to-port 8000
    iptables -t nat -A PREROUTING -i $WLAN_INTERFACE -p tcp --dport 443 -j REDIRECT --to-port 8000
    
    # Enable forwarding
    echo 1 > /proc/sys/net/ipv4/ip_forward
}

# Start AP mode
start_ap_mode() {
    log "========================================="
    log "Starting CloudPrintd Setup Mode (WiFi AP)"
    log "========================================="
    
    # Setup configurations
    setup_hostapd
    setup_dnsmasq
    setup_ap_interface
    
    # Start services
    log "Starting hostapd..."
    systemctl unmask hostapd 2>/dev/null || true
    systemctl start hostapd
    
    log "Starting dnsmasq..."
    systemctl start dnsmasq
    
    # Setup captive portal
    setup_captive_portal
    
    local suffix=$(generate_ssid_suffix)
    log "========================================="
    log "WiFi AP Active!"
    log "SSID: ${AP_SSID_PREFIX}-${suffix}"
    log "Password: $AP_PASSWORD"
    log "IP: $AP_IP"
    log "URL: http://$AP_IP:8000/setup"
    log "========================================="
    
    # Set environment variable for CloudPrintd
    export CLOUDPRINTD_AP_MODE=true
}

# Start normal WiFi mode
start_normal_mode() {
    log "WiFi configured - starting normal mode"
    
    # Ensure hostapd and dnsmasq are stopped
    systemctl stop hostapd 2>/dev/null || true
    systemctl stop dnsmasq 2>/dev/null || true
    
    # Clear any AP mode iptables rules
    iptables -t nat -F PREROUTING 2>/dev/null || true
    
    # Start wpa_supplicant
    systemctl start wpa_supplicant 2>/dev/null || true
    
    log "Normal WiFi mode active"
}

# Main execution
main() {
    log "========================================="
    log "CloudPrintd WiFi Setup Check Starting"
    log "========================================="
    
    # Check if WiFi interface exists
    if [ ! -d "/sys/class/net/$WLAN_INTERFACE" ]; then
        log "ERROR: WiFi interface $WLAN_INTERFACE not found"
        log "Skipping WiFi setup"
        exit 0
    fi
    
    # Check if WiFi is configured
    if is_wifi_configured; then
        log "WiFi is configured in $WPA_CONF"
        start_normal_mode
    else
        log "No WiFi configuration found"
        start_ap_mode
    fi
    
    log "WiFi setup check complete"
}

# Run main function
main

exit 0
