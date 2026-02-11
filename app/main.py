"""
CloudPrintd FastAPI Application
Main entry point for the print server API.
"""
import logging
import os
import secrets
import time
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.models import (
    PrintRequest, PrintResponse, PrinterInfo, PrinterConfig, PrinterStatus,
    DiscoveredPrinter, HealthResponse, StatsResponse, AddPrinterRequest,
    PrintFormat, PrinterType, VersionInfo, UpdateConfig
)
from app.config import ConfigManager
from app.security import SecurityManager, verify_token, verify_ip_whitelist
from app.printer import (
    send_zpl_raw, send_to_cups, check_printer_status,
    probe_zebra_printer, discover_zebra_printers
)
from update_manager.manager import UpdateManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application state
app_start_time = time.time()
job_stats = {
    "total_jobs": 0,
    "successful_jobs": 0,
    "failed_jobs": 0,
    "jobs_today": 0,
    "by_printer": {},
    "last_reset": datetime.utcnow().date().isoformat()
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("CloudPrintd starting up...")
    yield
    logger.info("CloudPrintd shutting down...")


# Initialise FastAPI app
app = FastAPI(
    title="CloudPrintd Print Server",
    description="Self-hosted print server for Salesforce cloud to on-site printers",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialise managers
config_dir = os.getenv("CONFIG_DIR", "config")
config_manager = ConfigManager(config_dir=config_dir)
security_manager = SecurityManager(config_manager)
update_manager = UpdateManager()

# Import and include network router
from app.routers.network import router as network_router
app.include_router(network_router, prefix="/api/v1")


# Dependency for authentication
async def require_auth(request: Request) -> str:
    """Dependency that requires authentication."""
    # Check IP whitelist
    await verify_ip_whitelist(request.client.host, security_manager)
    
    # Skip token check if setup not completed (for initial setup)
    if not config_manager.is_setup_completed():
        return "setup_mode"
    
    # Verify token
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    security = HTTPBearer()
    credentials = await security(request)
    return await verify_token(credentials, security_manager)


# Helper functions
def generate_job_id() -> str:
    """Generate a unique job ID."""
    return f"job_{int(time.time())}_{secrets.token_hex(4)}"


def update_stats(printer_id: str, success: bool) -> None:
    """Update job statistics."""
    global job_stats
    
    # Reset daily stats if needed
    today = datetime.utcnow().date().isoformat()
    if job_stats["last_reset"] != today:
        job_stats["jobs_today"] = 0
        job_stats["last_reset"] = today
    
    job_stats["total_jobs"] += 1
    job_stats["jobs_today"] += 1
    
    if success:
        job_stats["successful_jobs"] += 1
    else:
        job_stats["failed_jobs"] += 1
    
    if printer_id not in job_stats["by_printer"]:
        job_stats["by_printer"][printer_id] = 0
    job_stats["by_printer"][printer_id] += 1


# API Endpoints

@app.get("/", tags=["General"])
async def root():
    """Root endpoint."""
    return {
        "service": "CloudPrintd Print Server",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Used for update rollback verification.
    """
    printers_data = config_manager.get_printers()
    printers = printers_data.get("printers", {})
    
    # Count online printers
    printers_online = 0
    for printer_config in printers.values():
        status_result = await check_printer_status(printer_config)
        if status_result == "online":
            printers_online += 1
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=time.time() - app_start_time,
        printers_configured=len(printers),
        printers_online=printers_online
    )


@app.get("/api/v1/stats", response_model=StatsResponse, tags=["Health"])
async def get_stats(token: str = Depends(require_auth)):
    """Get print job statistics."""
    return StatsResponse(**job_stats)


@app.post("/api/v1/print", response_model=PrintResponse, tags=["Printing"])
async def submit_print_job(
    request: PrintRequest,
    token: str = Depends(require_auth)
):
    """
    Submit a print job.
    
    Accepts ZPL, PDF (base64), raw text, and routes to the appropriate printer.
    """
    job_id = generate_job_id()
    printer_id = request.printer
    
    logger.info(f"Received print job {job_id} for printer '{printer_id}'")
    
    # Get printer configuration
    printers = config_manager.get_printers()
    printer_config = printers.get("printers", {}).get(printer_id)
    
    if not printer_config:
        update_stats(printer_id, False)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer '{printer_id}' not found"
        )
    
    printer_type = printer_config.get("type")
    job_name = request.job_name or job_id
    
    try:
        # Handle multiple copies
        for copy_num in range(request.copies):
            if printer_type == PrinterType.ZEBRA_RAW:
                # Send via raw TCP
                ip = printer_config.get("ip")
                port = printer_config.get("port", 9100)
                
                if not ip:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Printer configuration missing IP address"
                    )
                
                result = await send_zpl_raw(ip, port, request.content)
                
                if not result.get("success"):
                    update_stats(printer_id, False)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=result.get("message", "Failed to send print job")
                    )
                    
            elif printer_type == PrinterType.CUPS:
                # Send via CUPS
                cups_name = printer_config.get("cups_name")
                
                if not cups_name:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Printer configuration missing CUPS name"
                    )
                
                result = await send_to_cups(cups_name, request.content, job_name)
                
                if not result.get("success"):
                    update_stats(printer_id, False)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=result.get("message", "Failed to send print job")
                    )
            else:
                update_stats(printer_id, False)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported printer type: {printer_type}"
                )
        
        update_stats(printer_id, True)
        
        return PrintResponse(
            job_id=job_id,
            status="completed",
            message=f"Successfully sent {request.copies} cop{'y' if request.copies == 1 else 'ies'} to printer",
            printer=printer_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing print job {job_id}: {e}", exc_info=True)
        update_stats(printer_id, False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@app.get("/api/v1/printers", response_model=List[PrinterInfo], tags=["Printers"])
async def list_printers(token: str = Depends(require_auth)):
    """List all configured printers with their status."""
    printers_data = config_manager.get_printers()
    printers = printers_data.get("printers", {})
    
    printer_list = []
    for printer_id, printer_config in printers.items():
        # Check printer status
        status_result = await check_printer_status(printer_config)
        
        printer_list.append(PrinterInfo(
            id=printer_id,
            config=PrinterConfig(**printer_config),
            status=PrinterStatus(status_result),
            last_check=datetime.utcnow().isoformat()
        ))
    
    return printer_list


@app.post("/api/v1/printers", status_code=status.HTTP_201_CREATED, tags=["Printers"])
async def add_printer(
    printer_request: AddPrinterRequest,
    token: str = Depends(require_auth)
):
    """Add a new printer configuration."""
    printer_id = printer_request.id
    printer_config = printer_request.config.dict()
    
    # Validate configuration based on type
    if printer_config["type"] == PrinterType.ZEBRA_RAW:
        if not printer_config.get("ip"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zebra printer requires IP address"
            )
    elif printer_config["type"] == PrinterType.CUPS:
        if not printer_config.get("cups_name"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CUPS printer requires cups_name"
            )
    
    # Add printer to configuration
    config_manager.add_printer(printer_id, printer_config)
    
    logger.info(f"Added printer '{printer_id}' of type '{printer_config['type']}'")
    
    return {
        "success": True,
        "message": f"Printer '{printer_id}' added successfully",
        "printer_id": printer_id
    }


@app.delete("/api/v1/printers/{printer_id}", tags=["Printers"])
async def remove_printer(
    printer_id: str,
    token: str = Depends(require_auth)
):
    """Remove a printer configuration."""
    success = config_manager.remove_printer(printer_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer '{printer_id}' not found"
        )
    
    logger.info(f"Removed printer '{printer_id}'")
    
    return {
        "success": True,
        "message": f"Printer '{printer_id}' removed successfully"
    }


@app.post("/api/v1/discover", response_model=List[DiscoveredPrinter], tags=["Printers"])
async def discover_printers(
    ip_range: str = "192.168.1.0/24",
    token: str = Depends(require_auth)
):
    """
    Scan network for Zebra printers.
    
    This endpoint probes port 9100 across the specified IP range.
    """
    logger.info(f"Starting printer discovery on {ip_range}")
    
    discovered = await discover_zebra_printers(ip_range)
    
    return [DiscoveredPrinter(**printer) for printer in discovered]


@app.post("/api/v1/setup/token", tags=["Setup"])
async def generate_token():
    """
    Generate a new API token.
    
    This endpoint is available during initial setup without authentication.
    """
    token = config_manager.generate_api_token()
    
    logger.info("Generated new API token")
    
    return {
        "success": True,
        "token": token,
        "message": "API token generated successfully. Store this securely."
    }


@app.post("/api/v1/setup/complete", tags=["Setup"])
async def complete_setup():
    """Mark initial setup as completed."""
    config_manager.mark_setup_completed()
    
    logger.info("Setup marked as completed")
    
    return {
        "success": True,
        "message": "Setup completed successfully"
    }


@app.get("/api/v1/setup/status", tags=["Setup"])
async def setup_status():
    """Check if setup is completed."""
    is_completed = config_manager.is_setup_completed()
    config = config_manager.get_config()
    
    return {
        "setup_completed": is_completed,
        "has_tokens": len(config.get("security", {}).get("api_tokens", [])) > 0,
        "printers_configured": len(config_manager.get_printers().get("printers", {}))
    }


@app.post("/api/v1/security/token/regenerate", tags=["Security"])
async def regenerate_api_token(token: str = Depends(require_auth)):
    """
    Generate a new API token (requires authentication with existing token).
    The old token will remain valid until you delete it.
    """
    new_token = config_manager.generate_api_token()
    
    logger.info("Generated additional API token")
    
    return {
        "success": True,
        "token": new_token,
        "message": "New API token generated. Store this securely. Your old token is still valid."
    }


@app.get("/api/v1/security/tokens", tags=["Security"])
async def list_api_tokens(token: str = Depends(require_auth)):
    """
    List all API tokens (masked for security).
    """
    config = config_manager.get_config()
    tokens = config.get("security", {}).get("api_tokens", [])
    
    # Mask tokens for security
    masked_tokens = []
    for i, tok in enumerate(tokens):
        masked_tokens.append({
            "id": i,
            "token": tok[:8] + "..." + tok[-4:] if len(tok) > 12 else "***",
            "created_at": config.get("security", {}).get("token_created_at", {}).get(str(i), "unknown")
        })
    
    return {
        "tokens": masked_tokens,
        "count": len(tokens)
    }


@app.delete("/api/v1/security/token/{token_index}", tags=["Security"])
async def delete_api_token(token_index: int, token: str = Depends(require_auth)):
    """
    Delete a specific API token by index.
    Warning: Cannot delete the last token or the token being used for this request.
    """
    config = config_manager.get_config()
    tokens = config.get("security", {}).get("api_tokens", [])
    
    if len(tokens) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last API token"
        )
    
    if token_index < 0 or token_index >= len(tokens):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token index not found"
        )
    
    # Check if trying to delete the token currently being used
    if tokens[token_index] == token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the token currently in use. Please use another token."
        )
    
    # Remove the token
    deleted_token = tokens.pop(token_index)
    config_manager.update_security_config({"api_tokens": tokens})
    
    logger.info(f"Deleted API token at index {token_index}")
    
    return {
        "success": True,
        "message": f"API token deleted successfully",
        "remaining_tokens": len(tokens)
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "message": "Internal server error"
        }
    )

# Update Management Endpoints

@app.get("/api/v1/system/version", tags=["System"])
async def get_version_info(token: str = Depends(require_auth)):
    """
    Get current version and check for updates.
    """
    current_version = update_manager.get_current_version()
    update_config = config_manager.get_update_config()
    
    # Check for updates
    update_available = None
    if update_config.get("auto_update"):
        update_info = await update_manager.check_for_updates(
            update_config["update_server"],
            update_config["channel"]
        )
        update_available = update_info
    
    return {
        "current_version": current_version,
        "update_available": update_available,
        "channel": update_config.get("channel", "stable"),
        "auto_update": update_config.get("auto_update", False)
    }


@app.get("/api/v1/system/versions", response_model=List[VersionInfo], tags=["System"])
async def list_versions(token: str = Depends(require_auth)):
    """
    List all available versions (installed + available from server).
    """
    update_config = config_manager.get_update_config()
    
    # Get available versions from server
    available_versions = await update_manager.list_available_versions(
        update_config["update_server"],
        update_config.get("channel", "stable")
    )
    
    # Get installed versions
    installed = update_manager.list_installed_versions()
    current = update_manager.get_current_version()
    
    # Merge data
    version_map = {}
    
    # Add server versions
    for ver in available_versions:
        version_map[ver["version"]] = VersionInfo(**ver)
    
    # Add any installed versions not on server
    for ver in installed:
        if ver not in version_map:
            version_map[ver] = VersionInfo(
                version=ver,
                channel="unknown",
                release_date="unknown",
                size_bytes=0,
                is_installed=True,
                is_current=(ver == current)
            )
    
    # Sort by version (descending)
    versions_list = sorted(
        version_map.values(),
        key=lambda v: v.version,
        reverse=True
    )
    
    return versions_list


@app.post("/api/v1/system/update/{version}", tags=["System"])
async def update_to_version(
    version: str,
    background_tasks: BackgroundTasks,
    token: str = Depends(require_auth)
):
    """
    Install and activate a specific version.
    This runs as a background task.
    """
    async def update_task():
        """Background task to perform the update."""
        try:
            logger.info(f"Starting update to version {version}")
            
            update_config = config_manager.get_update_config()
            
            # Check if already installed
            installed = update_manager.list_installed_versions()
            
            if version not in installed:
                # Download package
                logger.info(f"Downloading version {version}")
                package_path = await update_manager.download_package(
                    version,
                    update_config["update_server"]
                )
                
                if not package_path:
                    logger.error(f"Failed to download version {version}")
                    return
                
                # Install package
                logger.info(f"Installing version {version}")
                success = await update_manager.install_package(package_path, version)
                
                if not success:
                    logger.error(f"Failed to install version {version}")
                    return
            
            # Activate version
            logger.info(f"Activating version {version}")
            success = await update_manager.activate_version(version)
            
            if success:
                logger.info(f"Successfully updated to version {version}")
                
                # Cleanup old versions
                update_manager.cleanup_old_versions(
                    update_config.get("keep_previous_versions", 2)
                )
            else:
                logger.error(f"Failed to activate version {version}")
                
        except Exception as e:
            logger.error(f"Error during update task: {e}", exc_info=True)
    
    # Add task to background
    background_tasks.add_task(update_task)
    
    return {
        "success": True,
        "message": f"Update to version {version} started in background",
        "version": version
    }


@app.post("/api/v1/system/rollback", tags=["System"])
async def rollback_version(token: str = Depends(require_auth)):
    """
    Rollback to the previous version.
    """
    current = update_manager.get_current_version()
    installed = update_manager.list_installed_versions()
    
    # Remove current from list to find previous
    if current and current in installed:
        installed.remove(current)
    
    if not installed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No previous version available for rollback"
        )
    
    # Get most recent previous version
    previous_version = installed[0]
    
    logger.info(f"Rolling back from {current} to {previous_version}")
    
    success = await update_manager.rollback_to(previous_version)
    
    if success:
        return {
            "success": True,
            "message": f"Successfully rolled back to {previous_version}",
            "from_version": current,
            "to_version": previous_version
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rollback failed"
        )


@app.get("/api/v1/system/changelog/{version}", tags=["System"])
async def get_changelog(
    version: str,
    token: str = Depends(require_auth)
):
    """
    Get changelog for a specific version.
    """
    update_config = config_manager.get_update_config()
    
    changelog = await update_manager.get_changelog(
        version,
        update_config["update_server"]
    )
    
    if changelog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Changelog not found for version {version}"
        )
    
    return {
        "version": version,
        "changelog": changelog
    }


@app.get("/api/v1/system/update-config", response_model=UpdateConfig, tags=["System"])
async def get_update_config(token: str = Depends(require_auth)):
    """Get current update configuration."""
    config = config_manager.get_update_config()
    return UpdateConfig(**config)


@app.put("/api/v1/system/update-config", tags=["System"])
async def update_update_config(
    config: UpdateConfig,
    token: str = Depends(require_auth)
):
    """Update the update configuration settings."""
    config_manager.update_update_config(config.dict())
    
    return {
        "success": True,
        "message": "Update configuration updated successfully"
    }


@app.get("/api/v1/system/service/status", tags=["System"])
async def get_service_status(token: str = Depends(require_auth)):
    """
    Get service status (systemd status, uptime, etc).
    """
    try:
        import subprocess
        
        # Check if running under systemd
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "cloudprintd"],
                capture_output=True,
                text=True,
                timeout=5
            )
            systemd_status = result.stdout.strip()
            
            # Get detailed status
            status_result = subprocess.run(
                ["systemctl", "status", "cloudprintd", "--no-pager"],
                capture_output=True,
                text=True,
                timeout=5
            )
            status_output = status_result.stdout
            
        except (subprocess.SubprocessError, FileNotFoundError):
            systemd_status = "not-available"
            status_output = "systemctl not available or service not installed"
        
        # Calculate uptime
        uptime = time.time() - app_start_time
        
        return {
            "status": "running",
            "systemd_status": systemd_status,
            "uptime_seconds": int(uptime),
            "systemd_output": status_output if systemd_status != "not-available" else None,
            "version": update_manager.get_current_version() or "unknown"
        }
    
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return {
            "status": "running",
            "systemd_status": "unknown",
            "uptime_seconds": int(time.time() - app_start_time),
            "error": str(e),
            "version": update_manager.get_current_version() or "unknown"
        }


@app.post("/api/v1/system/service/restart", tags=["System"])
async def restart_service(token: str = Depends(require_auth)):
    """
    Request service restart. This will attempt to restart via systemd.
    Note: This endpoint may not return a response if the restart is immediate.
    """
    try:
        import subprocess
        
        # Try to restart via systemd
        try:
            subprocess.Popen(
                ["systemctl", "restart", "cloudprintd"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            return {
                "success": True,
                "message": "Restart command issued. Service will restart shortly."
            }
            
        except (subprocess.SubprocessError, FileNotFoundError):
            # If systemd not available, suggest manual restart
            return {
                "success": False,
                "message": "systemd not available. Please restart manually.",
                "manual_restart": "sudo systemctl restart cloudprintd"
            }
    
    except Exception as e:
        logger.error(f"Error restarting service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restarting service: {str(e)}"
        )


@app.get("/api/v1/system/service/logs", tags=["System"])
async def get_service_logs(
    lines: int = 100,
    token: str = Depends(require_auth)
):
    """
    Get recent service logs from journalctl or log files.
    
    Args:
        lines: Number of log lines to retrieve (default 100, max 500)
    """
    try:
        import subprocess
        from pathlib import Path
        
        # Limit lines
        lines = min(lines, 500)
        
        logs = []
        
        # Try journalctl first
        try:
            result = subprocess.run(
                ["journalctl", "-u", "cloudprintd", "-n", str(lines), "--no-pager"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logs = result.stdout.split('\n')
            
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Fallback to log files if journalctl not available
        if not logs:
            log_file = Path("/home/cloudprintd/logs/cloudprintd.log")
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = f.readlines()[-lines:]
            else:
                logs = ["Log files not found"]
        
        return {
            "lines": len(logs),
            "logs": logs
        }
    
    except Exception as e:
        logger.error(f"Error getting service logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving logs: {str(e)}"
        )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
