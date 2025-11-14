# app/utils/file_utils.py
"""
File utilities with safe cleanup.
"""
import os
import time
from typing import Optional


def safe_remove_file(file_path: str, max_retries: int = 3, retry_delay: float = 0.5) -> bool:
    """
    Safely remove file with retry logic.
    
    Args:
        file_path: Path to file to remove
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        bool: True if file was removed successfully
    """
    if not file_path or not os.path.exists(file_path):
        return True
    
    for attempt in range(max_retries):
        try:
            os.remove(file_path)
            print(f"   🗑️  Cleaned up: {os.path.basename(file_path)}")
            return True
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(f"   ⚠️  Cleanup attempt {attempt + 1}/{max_retries} failed, retrying...")
                time.sleep(retry_delay)
            else:
                print(f"   ❌ Failed to cleanup after {max_retries} attempts: {e}")
                return False
        except Exception as e:
            print(f"   ❌ Cleanup error: {e}")
            return False
    
    return False