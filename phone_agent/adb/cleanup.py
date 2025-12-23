"""Screenshot cleanup management module with retry, logging, and multi-device support."""

import subprocess
import time
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""
    success: bool
    message: str
    attempt: int
    total_attempts: int
    device_id: Optional[str] = None
    error_type: Optional[str] = None


class ScreenshotCleanupManager:
    """
    Manages cleanup of temporary screenshot files on Android devices.
    
    Features:
    - Automatic retry with exponential backoff
    - Comprehensive logging and error reporting
    - Multi-device support
    - Cleanup verification
    - Cleanup history tracking
    """
    
    # Configuration constants
    DEFAULT_SCREENSHOT_PATH = "/sdcard/tmp.png"
    DEFAULT_TIMEOUT = 5
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 0.5  # seconds
    
    def __init__(
        self,
        screenshot_path: str = DEFAULT_SCREENSHOT_PATH,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        verbose: bool = True,
    ):
        """
        Initialize the cleanup manager.
        
        Args:
            screenshot_path: Path to screenshot file on device (default: /sdcard/tmp.png)
            timeout: Timeout in seconds for ADB commands (default: 5)
            max_retries: Maximum number of cleanup attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 0.5)
            verbose: Whether to print detailed logs (default: True)
        """
        self.screenshot_path = screenshot_path
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.verbose = verbose
        self.cleanup_history = []
    
    def cleanup(self, device_id: Optional[str] = None) -> CleanupResult:
        """
        Clean up screenshot file on the specified device with retry logic.
        
        Args:
            device_id: Optional ADB device ID. If None, uses default device.
        
        Returns:
            CleanupResult with status, message, and attempt information.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                # Verify file exists before attempting cleanup
                exists = self._file_exists(device_id)
                if not exists:
                    result = CleanupResult(
                        success=True,
                        message="Screenshot file does not exist (already cleaned or never created)",
                        attempt=attempt,
                        total_attempts=self.max_retries,
                        device_id=device_id,
                    )
                    self._log(result, device_id)
                    return result
                
                # Attempt cleanup
                self._remove_file(device_id)
                
                # Verify cleanup success
                if self._file_exists(device_id):
                    # File still exists, retry
                    self._log_attempt(f"Cleanup attempt {attempt}/{self.max_retries}: File still exists", device_id)
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay * attempt)  # Exponential backoff
                        continue
                    
                    result = CleanupResult(
                        success=False,
                        message=f"File still exists after {self.max_retries} cleanup attempts",
                        attempt=attempt,
                        total_attempts=self.max_retries,
                        device_id=device_id,
                        error_type="cleanup_failed_file_persists",
                    )
                    self._log(result, device_id)
                    return result
                
                # Success
                result = CleanupResult(
                    success=True,
                    message=f"Screenshot cleaned up successfully (attempt {attempt}/{self.max_retries})",
                    attempt=attempt,
                    total_attempts=self.max_retries,
                    device_id=device_id,
                )
                self._log(result, device_id)
                return result
            
            except subprocess.TimeoutExpired:
                self._log_attempt(f"Cleanup attempt {attempt}/{self.max_retries}: ADB command timed out", device_id)
                if attempt == self.max_retries:
                    result = CleanupResult(
                        success=False,
                        message=f"Cleanup timed out after {self.max_retries} attempts",
                        attempt=attempt,
                        total_attempts=self.max_retries,
                        device_id=device_id,
                        error_type="cleanup_timeout",
                    )
                    self._log(result, device_id)
                    return result
                time.sleep(self.retry_delay * attempt)
            
            except Exception as e:
                self._log_attempt(f"Cleanup attempt {attempt}/{self.max_retries}: {type(e).__name__}: {str(e)}", device_id)
                if attempt == self.max_retries:
                    result = CleanupResult(
                        success=False,
                        message=f"Cleanup failed after {self.max_retries} attempts: {str(e)}",
                        attempt=attempt,
                        total_attempts=self.max_retries,
                        device_id=device_id,
                        error_type=type(e).__name__,
                    )
                    self._log(result, device_id)
                    return result
                time.sleep(self.retry_delay * attempt)
        
        # Should not reach here, but just in case
        result = CleanupResult(
            success=False,
            message=f"Cleanup failed: Unknown error",
            attempt=self.max_retries,
            total_attempts=self.max_retries,
            device_id=device_id,
            error_type="unknown",
        )
        self._log(result, device_id)
        return result
    
    def cleanup_all_devices(self) -> list[CleanupResult]:
        """
        Clean up screenshot files on all connected devices.
        
        Returns:
            List of CleanupResult for each device.
        """
        devices = self._get_connected_devices()
        results = []
        
        for device_id in devices:
            result = self.cleanup(device_id)
            results.append(result)
        
        return results
    
    def cleanup_stale_files(
        self,
        device_id: Optional[str] = None,
        max_age_hours: int = 24,
    ) -> CleanupResult:
        """
        Clean up screenshot file only if it's older than specified age.
        
        Useful for removing leftover files from previous failed cleanups.
        
        Args:
            device_id: Optional ADB device ID.
            max_age_hours: Only clean if file is older than this many hours.
        
        Returns:
            CleanupResult with status information.
        """
        try:
            adb_prefix = self._get_adb_prefix(device_id)
            
            # Get file modification time
            result = subprocess.run(
                adb_prefix + ["shell", "stat", "-c", "%Y", self.screenshot_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            if result.returncode != 0:
                # File doesn't exist or stat failed
                return CleanupResult(
                    success=True,
                    message="File does not exist or cannot stat",
                    attempt=1,
                    total_attempts=1,
                    device_id=device_id,
                )
            
            try:
                file_mtime = int(result.stdout.strip())
                current_time = int(time.time())
                age_seconds = current_time - file_mtime
                age_hours = age_seconds / 3600
                
                if age_hours >= max_age_hours:
                    self._log_attempt(f"File is {age_hours:.1f} hours old, cleaning up", device_id)
                    return self.cleanup(device_id)
                else:
                    result_obj = CleanupResult(
                        success=True,
                        message=f"File is only {age_hours:.1f} hours old (threshold: {max_age_hours}h), skipping cleanup",
                        attempt=1,
                        total_attempts=1,
                        device_id=device_id,
                    )
                    self._log(result_obj, device_id)
                    return result_obj
            except ValueError:
                return CleanupResult(
                    success=False,
                    message="Could not parse file modification time",
                    attempt=1,
                    total_attempts=1,
                    device_id=device_id,
                    error_type="parse_error",
                )
        
        except Exception as e:
            return CleanupResult(
                success=False,
                message=f"Failed to check file age: {str(e)}",
                attempt=1,
                total_attempts=1,
                device_id=device_id,
                error_type=type(e).__name__,
            )
    
    def get_file_info(self, device_id: Optional[str] = None) -> dict:
        """
        Get information about the screenshot file on the device.
        
        Args:
            device_id: Optional ADB device ID.
        
        Returns:
            Dictionary with file information (size, mtime, exists, etc.)
        """
        try:
            adb_prefix = self._get_adb_prefix(device_id)
            
            # Check if file exists and get size
            result = subprocess.run(
                adb_prefix + ["shell", "ls", "-la", self.screenshot_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            if result.returncode != 0 or "No such file" in result.stderr:
                return {
                    "exists": False,
                    "device_id": device_id,
                    "path": self.screenshot_path,
                }
            
            # Parse ls output: -rw-rw---- 1 root sdcard_rw 2097152 Dec 20 10:30 /sdcard/tmp.png
            parts = result.stdout.split()
            if len(parts) >= 5:
                try:
                    size = int(parts[4])
                except ValueError:
                    size = 0
            else:
                size = 0
            
            return {
                "exists": True,
                "device_id": device_id,
                "path": self.screenshot_path,
                "size": size,
                "size_mb": round(size / (1024 * 1024), 2),
                "raw_output": result.stdout.strip(),
            }
        
        except Exception as e:
            return {
                "exists": False,
                "device_id": device_id,
                "path": self.screenshot_path,
                "error": str(e),
            }
    
    def get_cleanup_history(self) -> list[dict]:
        """Get the cleanup attempt history."""
        return self.cleanup_history.copy()
    
    # Private helper methods
    
    def _file_exists(self, device_id: Optional[str] = None) -> bool:
        """Check if screenshot file exists on the device."""
        try:
            adb_prefix = self._get_adb_prefix(device_id)
            result = subprocess.run(
                adb_prefix + ["shell", "test", "-f", self.screenshot_path],
                capture_output=True,
                timeout=self.timeout,
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _remove_file(self, device_id: Optional[str] = None) -> None:
        """Remove screenshot file from the device."""
        adb_prefix = self._get_adb_prefix(device_id)
        subprocess.run(
            adb_prefix + ["shell", "rm", "-f", self.screenshot_path],
            capture_output=True,
            timeout=self.timeout,
        )
    
    def _get_connected_devices(self) -> list[str]:
        """Get list of connected ADB device IDs."""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            devices = []
            for line in result.stdout.split("\n")[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
            return devices
        except Exception:
            return []
    
    @staticmethod
    def _get_adb_prefix(device_id: Optional[str] = None) -> list:
        """Get ADB command prefix with optional device specifier."""
        if device_id:
            return ["adb", "-s", device_id]
        return ["adb"]
    
    def _log(self, result: CleanupResult, device_id: Optional[str] = None) -> None:
        """Log cleanup result to history and optionally print."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "device_id": result.device_id or device_id,
            "success": result.success,
            "message": result.message,
            "attempt": result.attempt,
            "total_attempts": result.total_attempts,
            "error_type": result.error_type,
        }
        self.cleanup_history.append(log_entry)
        
        if self.verbose:
            status_icon = "✅" if result.success else "❌"
            print(f"{status_icon} Cleanup ({result.attempt}/{result.total_attempts}): {result.message}")
    
    def _log_attempt(self, message: str, device_id: Optional[str] = None) -> None:
        """Log an intermediate attempt message."""
        if self.verbose:
            print(f"⏳ {message}")
