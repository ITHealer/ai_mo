import base64
import io
import warnings
import requests
from PIL import Image
from typing import Optional


def suppress_warnings():
    """Suppress common warnings from libraries"""
    warnings.filterwarnings("ignore", message="Using a target size.*", category=UserWarning)
    warnings.filterwarnings("ignore", message="Trying to unscale the audios.*", category=UserWarning)


def image_to_base64(image: Image.Image, quality: int = 85) -> str:
    """
    Convert PIL Image to base64 encoded JPEG string.
    
    Args:
        image: PIL Image object
        quality: JPEG quality (1-100)
        
    Returns:
        Base64 encoded string
    """
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def base64_to_image(base64_string: str) -> Optional[Image.Image]:
    """
    Convert base64 string to PIL Image.
    
    Args:
        base64_string: Base64 encoded image string
        
    Returns:
        PIL Image object or None if invalid
    """
    try:
        # Remove data URL prefix if present
        if "base64," in base64_string:
            base64_string = base64_string.split("base64,")[1]
        
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        return image
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        return None


def download_image_from_url(image_url: str, timeout: int = 10) -> Optional[Image.Image]:
    """
    Download image from URL.
    
    Args:
        image_url: URL to image file
        timeout: Request timeout in seconds
        
    Returns:
        PIL Image object or None if error
    """
    try:
        response = requests.get(image_url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        image = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        return image
    except Exception as e:
        print(f"Error downloading image from URL: {e}")
        return None


def validate_image(image: Image.Image) -> bool:
    """
    Validate image format and size.
    
    Args:
        image: PIL Image object
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check dimensions (max 4096x4096)
        width, height = image.size
        if width > 4096 or height > 4096:
            return False
        
        # Check if image has valid size
        if width < 1 or height < 1:
            return False
            
        return True
    except Exception:
        return False