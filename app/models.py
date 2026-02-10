"""
Pydantic models for request and response validation.
"""
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from enum import Enum


class PrintFormat(str, Enum):
    """Supported print formats."""
    ZPL = "zpl"
    PDF = "pdf"
    RAW = "raw"
    TEXT = "text"


class PrinterType(str, Enum):
    """Supported printer types."""
    ZEBRA_RAW = "zebra_raw"
    CUPS = "cups"


class PrinterStatus(str, Enum):
    """Printer status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    UNKNOWN = "unknown"


class PrintRequest(BaseModel):
    """Request model for print job submission."""
    printer: str = Field(..., description="Printer identifier")
    content: str = Field(..., description="Print content (ZPL, PDF base64, or text)")
    format: PrintFormat = Field(default=PrintFormat.ZPL, description="Content format")
    copies: int = Field(default=1, ge=1, le=100, description="Number of copies")
    job_name: Optional[str] = Field(default=None, description="Optional job name")


class PrintResponse(BaseModel):
    """Response model for print job submission."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
    printer: str = Field(..., description="Printer name")


class PrinterConfig(BaseModel):
    """Printer configuration model."""
    type: PrinterType = Field(..., description="Printer type")
    display_name: str = Field(..., description="Human-readable printer name")
    location: Optional[str] = Field(default=None, description="Physical location")
    # Zebra-specific fields
    ip: Optional[str] = Field(default=None, description="IP address for raw TCP printers")
    port: Optional[int] = Field(default=9100, description="TCP port for raw printers")
    # CUPS-specific fields
    cups_name: Optional[str] = Field(default=None, description="CUPS printer name")


class PrinterInfo(BaseModel):
    """Printer information response."""
    id: str = Field(..., description="Printer identifier")
    config: PrinterConfig = Field(..., description="Printer configuration")
    status: PrinterStatus = Field(..., description="Current printer status")
    last_check: Optional[str] = Field(default=None, description="Last status check timestamp")


class DiscoveredPrinter(BaseModel):
    """Model for discovered printer during network scan."""
    ip: str = Field(..., description="IP address")
    port: int = Field(..., description="Port number")
    type: str = Field(..., description="Detected printer type")
    responding: bool = Field(..., description="Whether printer responded")


class HealthResponse(BaseModel):
    """System health check response."""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    printers_configured: int = Field(..., description="Number of configured printers")
    printers_online: int = Field(..., description="Number of online printers")


class StatsResponse(BaseModel):
    """Print job statistics response."""
    total_jobs: int = Field(..., description="Total jobs processed")
    successful_jobs: int = Field(..., description="Successful jobs")
    failed_jobs: int = Field(..., description="Failed jobs")
    jobs_today: int = Field(..., description="Jobs processed today")
    by_printer: Dict[str, int] = Field(default_factory=dict, description="Jobs by printer")


class AddPrinterRequest(BaseModel):
    """Request to add a new printer."""
    id: str = Field(..., description="Unique printer identifier")
    config: PrinterConfig = Field(..., description="Printer configuration")


class VersionInfo(BaseModel):
    """Version information model."""
    version: str = Field(..., description="Version number")
    channel: str = Field(..., description="Release channel")
    release_date: str = Field(..., description="Release date")
    size_bytes: int = Field(..., description="Package size")
    changelog: Optional[str] = Field(default=None, description="Changelog text")
    is_installed: bool = Field(default=False, description="Whether version is installed")
    is_current: bool = Field(default=False, description="Whether version is active")


class UpdateConfig(BaseModel):
    """Update configuration model."""
    auto_update: bool = Field(..., description="Enable automatic updates")
    channel: str = Field(..., description="Release channel (stable/beta/dev)")
    check_interval_hours: int = Field(..., ge=1, le=168, description="Update check interval")
    keep_previous_versions: int = Field(..., ge=1, le=5, description="Number of versions to keep")
    update_server: str = Field(..., description="Update server URL")
