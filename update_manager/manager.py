"""
Update Manager for CloudPrintd
Handles version management, updates, rollbacks, and package installation.
"""
import os
import json
import hashlib
import tarfile
import shutil
import logging
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class UpdateManager:
    """Manages package updates, installations, and version control."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialise update manager.
        
        Args:
            base_dir: Base directory for CloudPrintd data (defaults to env var or /home/cloudprintd/data)
        """
        if base_dir is None:
            base_dir = os.getenv("DATA_DIR", "/home/cloudprintd/data")
        
        self.base_dir = Path(base_dir)
        self.packages_dir = self.base_dir / "packages"
        self.downloads_dir = self.base_dir / "downloads"
        self.current_link = self.packages_dir / "current"
        
        # Ensure directories exist
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"UpdateManager initialised with base_dir: {base_dir}")
    
    def get_current_version(self) -> Optional[str]:
        """
        Get the currently active version.
        
        Returns:
            Version string or None if no version is active
        """
        try:
            if self.current_link.is_symlink():
                target = self.current_link.resolve()
                return target.name
            return None
        except Exception as e:
            logger.error(f"Error reading current version: {e}")
            return None
    
    def list_installed_versions(self) -> List[str]:
        """
        List all installed versions.
        
        Returns:
            List of version strings
        """
        try:
            versions = []
            if self.packages_dir.exists():
                for item in self.packages_dir.iterdir():
                    if item.is_dir() and item.name != "current":
                        versions.append(item.name)
            return sorted(versions, reverse=True)
        except Exception as e:
            logger.error(f"Error listing installed versions: {e}")
            return []
    
    async def check_for_updates(self, update_server: str, 
                                channel: str = "stable") -> Optional[Dict[str, Any]]:
        """
        Check update server for available updates.
        
        Args:
            update_server: Update server URL
            channel: Release channel (stable/beta/dev)
            
        Returns:
            Update information dictionary or None
        """
        try:
            import httpx
            
            current_version = self.get_current_version()
            
            url = f"{update_server}/api/v1/updates"
            params = {
                "current_version": current_version or "0.0.0",
                "channel": channel
            }
            
            logger.info(f"Checking for updates from {url}")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return None
    
    async def list_available_versions(self, update_server: str, 
                                     channel: str = "stable") -> List[Dict[str, Any]]:
        """
        List all available versions from update server.
        
        Args:
            update_server: Update server URL
            channel: Release channel
            
        Returns:
            List of version information dictionaries
        """
        try:
            import httpx
            
            url = f"{update_server}/api/v1/versions"
            params = {"channel": channel}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Mark installed versions
                installed = self.list_installed_versions()
                current = self.get_current_version()
                
                for version in data.get("versions", []):
                    version["is_installed"] = version["version"] in installed
                    version["is_current"] = version["version"] == current
                
                return data.get("versions", [])
                
        except Exception as e:
            logger.error(f"Error listing available versions: {e}")
            return []
    
    async def download_package(self, version: str, update_server: str) -> Optional[Path]:
        """
        Download a package from the update server.
        
        Args:
            version: Version to download
            update_server: Update server URL
            
        Returns:
            Path to downloaded package or None on failure
        """
        try:
            import httpx
            
            # Get package info
            url = f"{update_server}/api/v1/package/{version}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                package_info = response.json()
            
            download_url = package_info.get("download_url")
            expected_checksum = package_info.get("checksum")
            
            if not download_url:
                logger.error("No download URL in package info")
                return None
            
            # Make URL absolute if relative
            if not download_url.startswith("http"):
                download_url = f"{update_server}{download_url}"
            
            # Download package
            package_path = self.downloads_dir / f"CloudPrintd-{version}.pbpkg"
            
            logger.info(f"Downloading {download_url} to {package_path}")
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()
                    
                    with open(package_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
            
            # Verify checksum
            if expected_checksum:
                actual_checksum = self._calculate_checksum(package_path)
                if actual_checksum != expected_checksum:
                    logger.error(f"Checksum mismatch for {version}")
                    package_path.unlink()
                    return None
                logger.info(f"Checksum verified for {version}")
            
            return package_path
            
        except Exception as e:
            logger.error(f"Error downloading package {version}: {e}")
            return None
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate SHA256 checksum of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of checksum
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    async def install_package(self, package_path: Path, version: str) -> bool:
        """
        Install a package to the packages directory.
        
        Args:
            package_path: Path to .pbpkg file
            version: Version string
            
        Returns:
            True if installation successful
        """
        try:
            version_dir = self.packages_dir / version
            
            # Check if version already installed
            if version_dir.exists():
                logger.warning(f"Version {version} already installed, removing old installation")
                shutil.rmtree(version_dir)
            
            # Create version directory
            version_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Extracting package to {version_dir}")
            
            # Extract tarball
            with tarfile.open(package_path, 'r:gz') as tar:
                tar.extractall(version_dir)
            
            # Read and verify manifest
            manifest_path = version_dir / "manifest.json"
            if not manifest_path.exists():
                logger.error("Package missing manifest.json")
                shutil.rmtree(version_dir)
                return False
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Verify checksums if present
            checksums = manifest.get("checksums", {})
            if checksums:
                logger.info("Verifying package checksums...")
                for file_path, expected_checksum in checksums.items():
                    full_path = version_dir / file_path
                    if full_path.exists():
                        actual_checksum = self._calculate_checksum(full_path)
                        if actual_checksum != expected_checksum:
                            logger.error(f"Checksum mismatch for {file_path}")
                            shutil.rmtree(version_dir)
                            return False
            
            # Run pre-install hook if exists
            await self._run_hook(version_dir, "pre-install.sh")
            
            # Set up virtual environment
            self._setup_virtualenv(version_dir)
            
            # Run post-install hook if exists
            await self._run_hook(version_dir, "post-install.sh")
            
            logger.info(f"Successfully installed version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Error installing package {version}: {e}", exc_info=True)
            # Clean up on failure
            version_dir = self.packages_dir / version
            if version_dir.exists():
                shutil.rmtree(version_dir)
            return False
    
    def _setup_virtualenv(self, version_dir: Path) -> None:
        """
        Set up Python virtual environment for a version.
        
        Args:
            version_dir: Path to version directory
        """
        venv_dir = version_dir / "venv"
        requirements_file = version_dir / "app" / "requirements.txt"
        
        if not requirements_file.exists():
            logger.warning(f"No requirements.txt found in {version_dir}")
            return
        
        try:
            logger.info(f"Creating virtual environment in {venv_dir}")
            
            # Create venv
            subprocess.run(
                ["python3", "-m", "venv", str(venv_dir)],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Get pip path
            pip_path = venv_dir / "bin" / "pip"
            if not pip_path.exists():
                pip_path = venv_dir / "Scripts" / "pip.exe"  # Windows
            
            # Install requirements
            logger.info(f"Installing requirements from {requirements_file}")
            subprocess.run(
                [str(pip_path), "install", "-r", str(requirements_file)],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info("Virtual environment setup complete")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error setting up virtualenv: {e.stderr}")
            raise
    
    async def _run_hook(self, version_dir: Path, hook_name: str) -> bool:
        """
        Run a lifecycle hook script.
        
        Args:
            version_dir: Path to version directory
            hook_name: Hook script name
            
        Returns:
            True if hook ran successfully or doesn't exist
        """
        hook_path = version_dir / "hooks" / hook_name
        
        if not hook_path.exists():
            logger.debug(f"Hook {hook_name} not found, skipping")
            return True
        
        try:
            logger.info(f"Running hook: {hook_name}")
            
            # Make executable
            os.chmod(hook_path, 0o755)
            
            # Run hook
            process = await asyncio.create_subprocess_exec(
                str(hook_path),
                cwd=str(version_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Hook {hook_name} failed: {stderr.decode()}")
                return False
            
            logger.info(f"Hook {hook_name} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running hook {hook_name}: {e}")
            return False
    
    async def activate_version(self, version: str) -> bool:
        """
        Activate a specific version (switch symlink).
        
        Args:
            version: Version to activate
            
        Returns:
            True if activation successful
        """
        try:
            version_dir = self.packages_dir / version
            
            if not version_dir.exists():
                logger.error(f"Version {version} not installed")
                return False
            
            # Get current version for rollback
            old_version = self.get_current_version()
            
            # Run pre-upgrade hook
            await self._run_hook(version_dir, "pre-upgrade.sh")
            
            # Create new symlink (atomic operation)
            new_link = self.packages_dir / f"current.{version}.tmp"
            new_link.symlink_to(version, target_is_directory=True)
            
            # Atomic rename
            new_link.replace(self.current_link)
            
            logger.info(f"Activated version {version}")
            
            # Run migrations if present
            await self._run_migrations(version_dir)
            
            # Run post-upgrade hook
            await self._run_hook(version_dir, "post-upgrade.sh")
            
            # Restart service (handled externally)
            logger.info(f"Version {version} activated successfully")
            
            # Verify health
            await asyncio.sleep(5)  # Give service time to start
            if not await self._verify_health():
                logger.error("Health check failed after activation, rolling back")
                if old_version:
                    await self.rollback_to(old_version)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error activating version {version}: {e}", exc_info=True)
            return False
    
    async def _run_migrations(self, version_dir: Path) -> bool:
        """
        Run database/config migrations.
        
        Args:
            version_dir: Path to version directory
            
        Returns:
            True if migrations ran successfully
        """
        migrations_dir = version_dir / "migrations"
        
        if not migrations_dir.exists():
            logger.debug("No migrations directory found")
            return True
        
        try:
            # Look for up.sql or other migration files
            up_sql = migrations_dir / "up.sql"
            
            if up_sql.exists():
                logger.info("Running SQL migrations")
                # TODO: Implement SQL migration logic if using a database
                # For now, this is a placeholder
            
            return True
            
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            return False
    
    async def _verify_health(self) -> bool:
        """
        Verify service health after activation.
        
        Returns:
            True if service is healthy
        """
        try:
            import httpx
            
            # Try to connect to health endpoint
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8000/api/v1/health")
                response.raise_for_status()
                data = response.json()
                return data.get("status") == "healthy"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def rollback_to(self, version: str) -> bool:
        """
        Rollback to a specific version.
        
        Args:
            version: Version to rollback to
            
        Returns:
            True if rollback successful
        """
        try:
            logger.warning(f"Rolling back to version {version}")
            
            version_dir = self.packages_dir / version
            
            if not version_dir.exists():
                logger.error(f"Cannot rollback: version {version} not installed")
                return False
            
            # Run rollback hook
            await self._run_hook(version_dir, "rollback.sh")
            
            # Activate the old version
            return await self.activate_version(version)
            
        except Exception as e:
            logger.error(f"Error during rollback to {version}: {e}", exc_info=True)
            return False
    
    def cleanup_old_versions(self, keep_count: int = 2) -> None:
        """
        Remove old versions beyond retention policy.
        
        Args:
            keep_count: Number of versions to keep
        """
        try:
            versions = self.list_installed_versions()
            current = self.get_current_version()
            
            # Always keep current version
            if current and current in versions:
                versions.remove(current)
            
            # Remove oldest versions
            if len(versions) > keep_count:
                to_remove = versions[keep_count:]
                
                for version in to_remove:
                    version_dir = self.packages_dir / version
                    logger.info(f"Removing old version {version}")
                    shutil.rmtree(version_dir)
                    
        except Exception as e:
            logger.error(f"Error cleaning up old versions: {e}")
    
    async def get_changelog(self, version: str, update_server: str) -> Optional[str]:
        """
        Get changelog for a specific version.
        
        Args:
            version: Version string
            update_server: Update server URL
            
        Returns:
            Changelog text or None
        """
        try:
            import httpx
            
            url = f"{update_server}/api/v1/changelog/{version}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
                
        except Exception as e:
            logger.error(f"Error fetching changelog for {version}: {e}")
            return None
