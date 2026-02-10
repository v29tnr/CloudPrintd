"""
Security middleware and utilities for CloudPrintd.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


class SecurityManager:
    """Manages API authentication and authorization."""
    
    def __init__(self, config_manager):
        """
        Initialise security manager.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config_manager = config_manager
    
    def validate_token(self, token: str) -> bool:
        """
        Validate API token.
        
        Args:
            token: Bearer token to validate
            
        Returns:
            True if token is valid
        """
        return self.config_manager.validate_token(token)
    
    def check_ip_whitelist(self, client_ip: str) -> bool:
        """
        Check if client IP is whitelisted.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            True if IP is allowed or whitelist is disabled
        """
        config = self.config_manager.get_config()
        security_config = config.get("security", {})
        
        if not security_config.get("ip_whitelist_enabled", False):
            return True
        
        whitelist = security_config.get("ip_whitelist", [])
        
        # Check if IP is in whitelist
        from ipaddress import ip_address, ip_network
        
        try:
            client = ip_address(client_ip)
            for allowed in whitelist:
                try:
                    # Support both single IPs and CIDR ranges
                    if '/' in allowed:
                        if client in ip_network(allowed, strict=False):
                            return True
                    else:
                        if client == ip_address(allowed):
                            return True
                except ValueError:
                    continue
        except ValueError:
            logger.warning(f"Invalid client IP format: {client_ip}")
            return False
        
        return False


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    security_manager: Optional[SecurityManager] = None
) -> str:
    """
    Verify bearer token from request.
    
    Args:
        credentials: HTTP authorization credentials
        security_manager: SecurityManager instance
        
    Returns:
        Validated token
        
    Raises:
        HTTPException: If token is invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    if security_manager and not security_manager.validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token


async def verify_ip_whitelist(
    client_ip: str,
    security_manager: SecurityManager
) -> None:
    """
    Verify client IP against whitelist.
    
    Args:
        client_ip: Client IP address
        security_manager: SecurityManager instance
        
    Raises:
        HTTPException: If IP is not whitelisted
    """
    if not security_manager.check_ip_whitelist(client_ip):
        logger.warning(f"Request from non-whitelisted IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP address not authorised"
        )
