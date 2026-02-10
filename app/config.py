"""
Configuration management for CloudPrintd.
"""
import json
import os
import secrets
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigManager:
    """Manages application configuration files."""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialise configuration manager.
        
        Args:
            config_dir: Path to configuration directory
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.printers_file = self.config_dir / "printers.json"
        self.update_file = self.config_dir / "update.json"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialise configs if they don't exist
        self._initialise_configs()
    
    def _initialise_configs(self) -> None:
        """Initialise configuration files with defaults if they don't exist."""
        # Main config
        if not self.config_file.exists():
            defaults_file = self.config_dir / "defaults.json"
            if defaults_file.exists():
                defaults = self._load_json(defaults_file)
            else:
                defaults = {
                    "api_version": "1.0.0",
                    "server": {
                        "host": "0.0.0.0",
                        "port": 8000,
                        "log_level": "info"
                    },
                    "security": {
                        "api_tokens": [],
                        "ip_whitelist_enabled": False,
                        "ip_whitelist": []
                    },
                    "connectivity": {
                        "method": "none",
                        "tunnel_token": "",
                        "tailscale_key": "",
                        "ddns_config": {},
                        "domain": ""
                    },
                    "system": {
                        "setup_completed": False,
                        "instance_id": secrets.token_hex(16)
                    }
                }
            self._save_json(self.config_file, defaults)
        
        # Printers config
        if not self.printers_file.exists():
            self._save_json(self.printers_file, {"printers": {}})
        
        # Update config
        if not self.update_file.exists():
            update_defaults = {
                "auto_update": False,
                "channel": "stable",
                "check_interval_hours": 24,
                "keep_previous_versions": 2,
                "update_server": "https://updates.CloudPrintd.local"
            }
            self._save_json(self.update_file, update_defaults)
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load {file_path}: {e}")
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save JSON to file atomically."""
        temp_file = file_path.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            # Atomic rename
            temp_file.replace(file_path)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise RuntimeError(f"Failed to save {file_path}: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get main configuration."""
        return self._load_json(self.config_file)
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update main configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        config = self.get_config()
        config.update(updates)
        self._save_json(self.config_file, config)
    
    def get_printers(self) -> Dict[str, Any]:
        """Get printers configuration."""
        return self._load_json(self.printers_file)
    
    def add_printer(self, printer_id: str, printer_config: Dict[str, Any]) -> None:
        """
        Add or update a printer configuration.
        
        Args:
            printer_id: Unique printer identifier
            printer_config: Printer configuration dictionary
        """
        printers = self.get_printers()
        printers["printers"][printer_id] = printer_config
        self._save_json(self.printers_file, printers)
    
    def remove_printer(self, printer_id: str) -> bool:
        """
        Remove a printer configuration.
        
        Args:
            printer_id: Printer identifier to remove
            
        Returns:
            True if printer was removed, False if not found
        """
        printers = self.get_printers()
        if printer_id in printers["printers"]:
            del printers["printers"][printer_id]
            self._save_json(self.printers_file, printers)
            return True
        return False
    
    def get_update_config(self) -> Dict[str, Any]:
        """Get update configuration."""
        return self._load_json(self.update_file)
    
    def update_update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update update configuration.
        
        Args:
            updates: Dictionary of update configuration changes
        """
        config = self.get_update_config()
        config.update(updates)
        self._save_json(self.update_file, config)
    
    def generate_api_token(self) -> str:
        """
        Generate a new API token and add it to configuration.
        
        Returns:
            The generated token
        """
        token = secrets.token_urlsafe(32)
        config = self.get_config()
        if "security" not in config:
            config["security"] = {}
        if "api_tokens" not in config["security"]:
            config["security"]["api_tokens"] = []
        config["security"]["api_tokens"].append(token)
        self._save_json(self.config_file, config)
        return token
    
    def validate_token(self, token: str) -> bool:
        """
        Validate an API token.
        
        Args:
            token: Token to validate
            
        Returns:
            True if token is valid
        """
        config = self.get_config()
        tokens = config.get("security", {}).get("api_tokens", [])
        return token in tokens
    
    def is_setup_completed(self) -> bool:
        """Check if initial setup is completed."""
        config = self.get_config()
        return config.get("system", {}).get("setup_completed", False)
    
    def mark_setup_completed(self) -> None:
        """Mark initial setup as completed."""
        config = self.get_config()
        if "system" not in config:
            config["system"] = {}
        config["system"]["setup_completed"] = True
        self._save_json(self.config_file, config)
