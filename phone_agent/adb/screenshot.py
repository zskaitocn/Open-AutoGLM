"""Screenshot utilities for capturing Android device screen."""

import base64
import os
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from io import BytesIO
from typing import Tuple

from PIL import Image


@dataclass
class Screenshot:
    """Represents a captured screenshot."""

    base64_data: str
    width: int
    height: int
    is_sensitive: bool = False


def _is_black_image(img: Image.Image, threshold: int = 20) -> bool:
    """
    Check if an image is mostly black (likely a failed screenshot).
    
    Args:
        img: PIL Image object.
        threshold: How many non-black pixels allowed before considering it not black.
    
    Returns:
        True if image is mostly black, False otherwise.
    """
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get image data
    pixels = list(img.getdata())
    
    # Count dark pixels (R, G, B all < 50)
    dark_pixels = sum(1 for r, g, b in pixels if r < 50 and g < 50 and b < 50)
    dark_ratio = dark_pixels / len(pixels)
    
    # If more than 95% of pixels are dark, it's a black image
    return dark_ratio > 0.95


def get_screenshot(device_id: str | None = None, timeout: int = 10, retry_count: int = 3) -> Screenshot:
    """
    Capture a screenshot from the connected Android device.

    Args:
        device_id: Optional ADB device ID for multi-device setups.
        timeout: Timeout in seconds for screenshot operations.
        retry_count: Number of times to retry if black image is detected.

    Returns:
        Screenshot object containing base64 data and dimensions.

    Note:
        If the screenshot fails (e.g., on sensitive screens like payment pages),
        a black fallback image is returned with is_sensitive=True.
    """
    for attempt in range(retry_count):
        temp_path = os.path.join(tempfile.gettempdir(), f"screenshot_{uuid.uuid4()}.png")
        adb_prefix = _get_adb_prefix(device_id)

        try:
            # Execute screenshot command
            result = subprocess.run(
                adb_prefix + ["shell", "screencap", "-p", "/sdcard/tmp.png"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Check for screenshot command failure (return code != 0)
            if result.returncode != 0:
                print(f"[screenshot.py] Screenshot command failed on attempt {attempt + 1}/{retry_count}: {result.stderr}")
                # Retry instead of immediately returning fallback
                if attempt < retry_count - 1:
                    import time
                    time.sleep(0.3)
                    continue
                # Only mark as sensitive if the error explicitly indicates it
                # (e.g., specific ADB errors related to permissions)
                is_sensitive_error = "Permission denied" in result.stderr or "error" in result.stderr.lower()
                print(f"[screenshot.py] All retries exhausted, returning fallback (is_sensitive={is_sensitive_error})")
                return _create_fallback_screenshot(is_sensitive=is_sensitive_error)

            # Pull screenshot to local temp path
            pull_result = subprocess.run(
                adb_prefix + ["pull", "/sdcard/tmp.png", temp_path],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if pull_result.returncode != 0 or not os.path.exists(temp_path):
                if attempt < retry_count - 1:
                    import time
                    time.sleep(0.2)
                    continue
                return _create_fallback_screenshot(is_sensitive=False)

            # Read and encode image
            try:
                img = Image.open(temp_path)
                width, height = img.size

                # Check if the image is mostly black (likely a screenshot failure, not sensitive)
                if _is_black_image(img):
                    print(f"[screenshot.py] Detected black image on attempt {attempt + 1}/{retry_count}, retrying...")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    # Retry on black image
                    if attempt < retry_count - 1:
                        import time
                        time.sleep(0.2)
                        continue
                    # After all retries, return non-sensitive fallback
                    print(f"[screenshot.py] All {retry_count} retries exhausted for black image, returning fallback")
                    return _create_fallback_screenshot(is_sensitive=False)

                buffered = BytesIO()
                img.save(buffered, format="PNG")
                base64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

                # Cleanup
                os.remove(temp_path)

                return Screenshot(
                    base64_data=base64_data, width=width, height=height, is_sensitive=False
                )
            except (OSError, IOError) as img_error:
                # Image file corrupted or unreadable
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if attempt < retry_count - 1:
                    import time
                    time.sleep(0.2)
                    continue
                return _create_fallback_screenshot(is_sensitive=False)

        except Exception as e:
            # Unexpected error - return non-sensitive fallback
            if attempt < retry_count - 1:
                import time
                time.sleep(0.2)
                continue
            return _create_fallback_screenshot(is_sensitive=False)
    
    # Fallback if all retries exhausted
    return _create_fallback_screenshot(is_sensitive=False)


def _get_adb_prefix(device_id: str | None) -> list:
    """Get ADB command prefix with optional device specifier."""
    if device_id:
        return ["adb", "-s", device_id]
    return ["adb"]


def _create_fallback_screenshot(is_sensitive: bool) -> Screenshot:
    """Create a black fallback image when screenshot fails."""
    default_width, default_height = 1080, 2400

    black_img = Image.new("RGB", (default_width, default_height), color="black")
    buffered = BytesIO()
    black_img.save(buffered, format="PNG")
    base64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return Screenshot(
        base64_data=base64_data,
        width=default_width,
        height=default_height,
        is_sensitive=is_sensitive,
    )


def cleanup_device_screenshots(device_id: str | None = None, verbose: bool = False) -> None:
    """
    Clean up temporary screenshot files on the Android device.

    This function removes the temporary screenshot file (/sdcard/tmp.png) that
    may have been created during agent operation. Uses retry logic and verification.

    Args:
        device_id: Optional ADB device ID for multi-device setups.
        verbose: Whether to print cleanup status messages (default: False).

    Raises:
        RuntimeError: If cleanup fails after all retries.
    """
    from phone_agent.adb.cleanup import ScreenshotCleanupManager
    
    # Use the new cleanup manager with retry logic
    manager = ScreenshotCleanupManager(verbose=verbose)
    result = manager.cleanup(device_id)
    
    if not result.success:
        raise RuntimeError(f"Failed to cleanup device screenshots: {result.message}")
