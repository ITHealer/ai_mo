import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from openai import OpenAI
from contextlib import asynccontextmanager
from typing import Optional
import tempfile

from src.utils.config import get_settings
from src.schemas.models import (
    TextModerationRequest,
    TextModerationResponse,
    ImageModerationResponse,
    VideoModerationResponse
)
from src.services.text_moderation import TextModerationService
from src.services.image_moderation import ImageModerationService
from src.services.asr_service import ASRService
from src.services.video_moderation import VideoModerationService
from src.utils.utils import suppress_warnings, base64_to_image, validate_image, download_image_from_url


# Global service instances
text_service: TextModerationService = None
image_service: ImageModerationService = None
video_service: VideoModerationService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global text_service, image_service, video_service
    
    settings = get_settings()
    suppress_warnings()
    
    print("\n" + "="*70)
    print(f"{settings.app_name} v{settings.app_version}")
    print("="*70)
    print(f"Configuration:")
    print(f"   Ollama Endpoint: {settings.ollama_base_url}")
    print(f"   Text Model: {settings.ollama_text_model}")
    print(f"   VLM Model: {settings.ollama_vlm_model}")
    print(f"   Device: {settings.device}")
    print("="*70)
    
    # Initialize Ollama client
    ollama_base_url = settings.ollama_base_url
    if not ollama_base_url.endswith('/v1'):
        ollama_base_url = f"{ollama_base_url}/v1"
    
    ollama_client = OpenAI(base_url=ollama_base_url, api_key="ollama")
    
    # Initialize services
    text_service = TextModerationService(ollama_client, settings.ollama_text_model)
    image_service = ImageModerationService(ollama_client, settings.ollama_vlm_model)
    asr_service = ASRService(settings.whisper_model_id, settings.device)
    video_service = VideoModerationService(
        text_service,
        image_service,
        asr_service
    )
    
    print("="*70)
    print("✨ All services initialized successfully!")
    print("="*70 + "\n")
    
    yield
    
    print("\n🔴 Shutting down services...")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Content moderation API for text, image, and video",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "text_moderation": text_service is not None,
            "image_moderation": image_service is not None,
            "video_moderation": video_service is not None
        }
    }


@app.post("/api/v1/moderate/text", response_model=TextModerationResponse)
async def moderate_text(request: TextModerationRequest):
    """
    Moderate text content.
    
    Args:
        request: TextModerationRequest with text to moderate
        
    Returns:
        TextModerationResponse with category and reasoning
    """
    try:
        result = text_service.moderate(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text moderation failed: {str(e)}")


@app.post("/api/v1/moderate/image", response_model=ImageModerationResponse)
async def moderate_image(
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    image_base64: Optional[str] = Form(None)
):
    """
    Moderate image content.
    
    Args:
        file: Image file (JPEG/PNG) - Optional
        image_url: URL to image - Optional
        image_base64: Base64 encoded image - Optional
        
    Note: Provide one of: file, image_url, or image_base64
        
    Returns:
        ImageModerationResponse with category and analysis
    """
    try:
        image = None
        
        # Priority: file > image_url > image_base64
        if file:
            # Read image from uploaded file
            from PIL import Image
            import io
            image_bytes = await file.read()
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
                
        elif image_url:
            # Download image from URL
            image = download_image_from_url(image_url)
            if not image:
                raise HTTPException(status_code=400, detail="Failed to download image from URL")
                
        elif image_base64:
            # Decode base64 image
            image = base64_to_image(image_base64)
            if not image:
                raise HTTPException(status_code=400, detail="Failed to decode base64 image")
        else:
            raise HTTPException(
                status_code=400,
                detail="No image provided. Please provide one of: file, image_url, or image_base64"
            )
        
        # Validate image
        if not validate_image(image):
            raise HTTPException(status_code=400, detail="Invalid image format or size (max 4096x4096)")
        
        # Moderate
        result = image_service.moderate(image)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image moderation failed: {str(e)}")


@app.post("/api/v1/moderate/video", response_model=VideoModerationResponse)
async def moderate_video(
    file: Optional[UploadFile] = File(None),
    video_url: Optional[str] = Form(None),
    sampling_fps: float = Form(0.5)
):
    """
    Moderate video content.
    
    Args:
        file: Video file - Optional
        video_url: URL to video file - Optional
        sampling_fps: Frame sampling rate (default: 0.5 fps)
        
    Note: Provide one of: file or video_url
        
    Returns:
        VideoModerationResponse with comprehensive analysis
    """
    temp_video_path = None
    
    try:
        # Priority: file > video_url
        if file:
            # Save uploaded video to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_video_path = temp_file.name
                content = await file.read()
                temp_file.write(content)
                
        elif video_url:
            # Download video from URL
            import requests
            response = requests.get(video_url, timeout=30, stream=True)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_video_path = temp_file.name
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
        else:
            raise HTTPException(
                status_code=400,
                detail="No video provided. Please provide one of: file or video_url"
            )
        
        # Moderate video
        result = video_service.moderate(temp_video_path, sampling_fps)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video moderation failed: {str(e)}")
    finally:
        # Clean up temp file
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
            except:
                pass


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.v1.content_moderation:app",
        host="0.0.0.0",
        port=8999,
        reload=settings.debug
    )