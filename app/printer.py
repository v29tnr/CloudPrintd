"""
Printer communication functions for Zebra ZPL and CUPS printers.
"""
import asyncio
import socket
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def send_zpl_raw(ip: str, port: int, zpl: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Send ZPL directly to Zebra printer via TCP socket.
    
    Args:
        ip: Printer IP address
        port: TCP port (usually 9100)
        zpl: ZPL content to print
        timeout: Connection timeout in seconds
        
    Returns:
        Dictionary with success status and message
    """
    try:
        logger.info(f"Sending ZPL to {ip}:{port}")
        
        # Create socket connection
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )
        
        # Send ZPL data
        writer.write(zpl.encode('utf-8'))
        await writer.drain()
        
        # Wait briefly for any response
        try:
            response = await asyncio.wait_for(reader.read(1024), timeout=2.0)
            response_text = response.decode('utf-8', errors='ignore') if response else ""
        except asyncio.TimeoutError:
            response_text = ""
        
        # Close connection
        writer.close()
        await writer.wait_closed()
        
        logger.info(f"Successfully sent ZPL to {ip}:{port}")
        return {
            "success": True,
            "message": f"Print job sent to {ip}:{port}",
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except asyncio.TimeoutError:
        error_msg = f"Connection timeout to {ip}:{port}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "error": "timeout",
            "timestamp": datetime.utcnow().isoformat()
        }
    except ConnectionRefusedError:
        error_msg = f"Connection refused by {ip}:{port}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "error": "connection_refused",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        error_msg = f"Error sending to {ip}:{port}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def send_to_cups(printer_name: str, content: str, job_name: str, 
                       content_type: str = "application/vnd.cups-raw") -> Dict[str, Any]:
    """
    Send job via CUPS for standard printers.
    
    Args:
        printer_name: CUPS printer name
        content: Content to print
        job_name: Job name/identifier
        content_type: MIME type of content
        
    Returns:
        Dictionary with success status and job ID
    """
    try:
        import cups
        
        logger.info(f"Sending job '{job_name}' to CUPS printer '{printer_name}'")
        
        # Connect to CUPS
        conn = cups.Connection()
        
        # Create a temporary file for the print job
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prn') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Submit print job
            job_id = conn.printFile(
                printer_name,
                tmp_path,
                job_name,
                {}
            )
            
            logger.info(f"CUPS job {job_id} submitted to {printer_name}")
            return {
                "success": True,
                "message": f"Print job submitted to CUPS",
                "job_id": job_id,
                "printer": printer_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            # Clean up temporary file
            import os
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
                
    except ImportError:
        error_msg = "CUPS support not available (pycups not installed)"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "error": "cups_unavailable",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        error_msg = f"Error printing to CUPS printer '{printer_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def check_printer_status(config: Dict[str, Any]) -> str:
    """
    Check if printer is online.
    
    Args:
        config: Printer configuration dictionary
        
    Returns:
        Status string: "online", "offline", "error", or "unknown"
    """
    try:
        printer_type = config.get("type")
        
        if printer_type == "zebra_raw":
            ip = config.get("ip")
            port = config.get("port", 9100)
            
            if not ip:
                return "error"
            
            # Try to probe the printer
            is_online = await probe_zebra_printer(ip, port)
            return "online" if is_online else "offline"
            
        elif printer_type == "cups":
            cups_name = config.get("cups_name")
            
            if not cups_name:
                return "error"
            
            # Check CUPS printer status
            try:
                import cups
                conn = cups.Connection()
                printers = conn.getPrinters()
                
                if cups_name in printers:
                    printer = printers[cups_name]
                    state = printer.get("printer-state", 0)
                    # State: 3 = idle (online), 4 = processing, 5 = stopped
                    if state in [3, 4]:
                        return "online"
                    else:
                        return "offline"
                else:
                    return "error"
                    
            except ImportError:
                return "unknown"
            except Exception as e:
                logger.error(f"Error checking CUPS printer status: {e}")
                return "error"
        else:
            return "unknown"
            
    except Exception as e:
        logger.error(f"Error checking printer status: {e}", exc_info=True)
        return "error"


async def probe_zebra_printer(ip: str, port: int = 9100, timeout: int = 3) -> bool:
    """
    Check if device at IP is a Zebra printer (try port 9100).
    
    Args:
        ip: IP address to probe
        port: TCP port to check (default 9100)
        timeout: Connection timeout in seconds
        
    Returns:
        True if printer responds on the port
    """
    try:
        # Try to establish TCP connection
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )
        
        # Send a simple ZPL query command to check if it's a Zebra printer
        # ~HI returns printer information
        writer.write(b'~HI\n')
        await writer.drain()
        
        # Wait for response
        try:
            response = await asyncio.wait_for(reader.read(1024), timeout=2.0)
            has_response = len(response) > 0
        except asyncio.TimeoutError:
            # No response is okay - connection was successful
            has_response = True
        
        # Close connection
        writer.close()
        await writer.wait_closed()
        
        return has_response
        
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False
    except Exception as e:
        logger.warning(f"Error probing {ip}:{port}: {e}")
        return False


async def discover_zebra_printers(ip_range: str = "192.168.1.0/24", 
                                  port: int = 9100) -> list:
    """
    Scan network for Zebra printers.
    
    Args:
        ip_range: IP range to scan (CIDR notation)
        port: Port to check (default 9100)
        
    Returns:
        List of discovered printer dictionaries
    """
    discovered = []
    
    try:
        # Parse IP range
        from ipaddress import IPv4Network
        network = IPv4Network(ip_range, strict=False)
        
        logger.info(f"Scanning {ip_range} for Zebra printers on port {port}")
        
        # Create tasks for parallel scanning
        tasks = []
        ips = []
        
        for ip in network.hosts():
            ip_str = str(ip)
            ips.append(ip_str)
            tasks.append(probe_zebra_printer(ip_str, port))
        
        # Run probes in parallel with limited concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect discovered printers
        for ip_str, result in zip(ips, results):
            if isinstance(result, bool) and result:
                discovered.append({
                    "ip": ip_str,
                    "port": port,
                    "type": "zebra_raw",
                    "responding": True
                })
        
        logger.info(f"Discovered {len(discovered)} printers")
        return discovered
        
    except Exception as e:
        logger.error(f"Error during printer discovery: {e}", exc_info=True)
        return discovered
