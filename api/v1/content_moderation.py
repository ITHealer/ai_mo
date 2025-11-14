# import os
# from fastapi import FastAPI, HTTPException, UploadFile, File, Form
# from fastapi.responses import JSONResponse
# from openai import OpenAI
# from contextlib import asynccontextmanager
# from typing import Optional
# import tempfile

# from src.utils.config import get_settings
# from src.schemas.models import (
#     TextModerationRequest,
#     TextModerationResponse,
#     ImageModerationResponse,
#     VideoModerationResponse
# )
# from src.services.text_moderation import TextModerationService
# from src.services.image_moderation import ImageModerationService
# from src.services.asr_service import ASRService
# from src.services.video_moderation import VideoModerationService
# from src.utils.utils import suppress_warnings, base64_to_image, validate_image, download_image_from_url


# # Global service instances
# text_service: TextModerationService = None
# image_service: ImageModerationService = None
# video_service: VideoModerationService = None


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Initialize services on startup"""
#     global text_service, image_service, video_service
    
#     settings = get_settings()
#     suppress_warnings()
    
#     print("\n" + "="*70)
#     print(f"{settings.app_name} v{settings.app_version}")
#     print("="*70)
#     print(f"Configuration:")
#     print(f"   Ollama Endpoint: {settings.ollama_base_url}")
#     print(f"   Text Model: {settings.ollama_text_model}")
#     print(f"   VLM Model: {settings.ollama_vlm_model}")
#     print(f"   Device: {settings.device}")
#     print("="*70)
    
#     # Initialize Ollama client
#     ollama_base_url = settings.ollama_base_url
#     if not ollama_base_url.endswith('/v1'):
#         ollama_base_url = f"{ollama_base_url}/v1"
    
#     ollama_client = OpenAI(base_url=ollama_base_url, api_key="ollama")
    
#     # Initialize services
#     text_service = TextModerationService(ollama_client, settings.ollama_text_model)
#     image_service = ImageModerationService(ollama_client, settings.ollama_vlm_model)
#     asr_service = ASRService(settings.whisper_model_id, settings.device)
#     video_service = VideoModerationService(
#         text_service,
#         image_service,
#         asr_service
#     )
    
#     print("="*70)
#     print("✨ All services initialized successfully!")
#     print("="*70 + "\n")
    
#     yield
    
#     print("\n🔴 Shutting down services...")


# # Create FastAPI app
# settings = get_settings()
# app = FastAPI(
#     title=settings.app_name,
#     version=settings.app_version,
#     description="Content moderation API for text, image, and video",
#     lifespan=lifespan
# )


# @app.get("/")
# async def root():
#     """Root endpoint"""
#     return {
#         "service": settings.app_name,
#         "version": settings.app_version,
#         "status": "operational"
#     }


# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     return {
#         "status": "healthy",
#         "services": {
#             "text_moderation": text_service is not None,
#             "image_moderation": image_service is not None,
#             "video_moderation": video_service is not None
#         }
#     }


# @app.post("/api/v1/moderate/text", response_model=TextModerationResponse)
# async def moderate_text(request: TextModerationRequest):
#     """
#     Moderate text content.
    
#     Args:
#         request: TextModerationRequest with text to moderate
        
#     Returns:
#         TextModerationResponse with category and reasoning
#     """
#     try:
#         result = text_service.moderate(request.text)
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Text moderation failed: {str(e)}")


# @app.post("/api/v1/moderate/image", response_model=ImageModerationResponse)
# async def moderate_image(
#     file: Optional[UploadFile] = File(None),
#     image_url: Optional[str] = Form(None),
#     image_base64: Optional[str] = Form(None)
# ):
#     """
#     Moderate image content.
    
#     Args:
#         file: Image file (JPEG/PNG) - Optional
#         image_url: URL to image - Optional
#         image_base64: Base64 encoded image - Optional
        
#     Note: Provide one of: file, image_url, or image_base64
        
#     Returns:
#         ImageModerationResponse with category and analysis
#     """
#     try:
#         image = None
        
#         # Priority: file > image_url > image_base64
#         if file:
#             # Read image from uploaded file
#             from PIL import Image
#             import io
#             image_bytes = await file.read()
#             image = Image.open(io.BytesIO(image_bytes))
            
#             # Convert to RGB if needed
#             if image.mode != "RGB":
#                 image = image.convert("RGB")
                
#         elif image_url:
#             # Download image from URL
#             image = download_image_from_url(image_url)
#             if not image:
#                 raise HTTPException(status_code=400, detail="Failed to download image from URL")
                
#         elif image_base64:
#             # Decode base64 image
#             image = base64_to_image(image_base64)
#             if not image:
#                 raise HTTPException(status_code=400, detail="Failed to decode base64 image")
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No image provided. Please provide one of: file, image_url, or image_base64"
#             )
        
#         # Validate image
#         if not validate_image(image):
#             raise HTTPException(status_code=400, detail="Invalid image format or size (max 4096x4096)")
        
#         # Moderate
#         result = image_service.moderate(image)
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Image moderation failed: {str(e)}")


# @app.post("/api/v1/moderate/video", response_model=VideoModerationResponse)
# async def moderate_video(
#     file: Optional[UploadFile] = File(None),
#     video_url: Optional[str] = Form(None),
#     sampling_fps: float = Form(0.5)
# ):
#     """
#     Moderate video content.
    
#     Args:
#         file: Video file - Optional
#         video_url: URL to video file - Optional
#         sampling_fps: Frame sampling rate (default: 0.5 fps)
        
#     Note: Provide one of: file or video_url
        
#     Returns:
#         VideoModerationResponse with comprehensive analysis
#     """
#     temp_video_path = None
    
#     try:
#         # Priority: file > video_url
#         if file:
#             # Save uploaded video to temp file
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
#                 temp_video_path = temp_file.name
#                 content = await file.read()
#                 temp_file.write(content)
                
#         elif video_url:
#             # Download video from URL
#             import requests
#             response = requests.get(video_url, timeout=30, stream=True)
#             response.raise_for_status()
            
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
#                 temp_video_path = temp_file.name
#                 for chunk in response.iter_content(chunk_size=8192):
#                     temp_file.write(chunk)
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No video provided. Please provide one of: file or video_url"
#             )
        
#         # Moderate video
#         result = video_service.moderate(temp_video_path, sampling_fps)
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Video moderation failed: {str(e)}")
#     finally:
#         # Clean up temp file
#         if temp_video_path and os.path.exists(temp_video_path):
#             try:
#                 os.remove(temp_video_path)
#             except:
#                 pass


# @app.exception_handler(Exception)
# async def global_exception_handler(request, exc):
#     """Global exception handler"""
#     return JSONResponse(
#         status_code=500,
#         content={
#             "error": "Internal server error",
#             "detail": str(exc)
#         }
#     )


# if __name__ == "__main__":
#     import uvicorn
    
#     uvicorn.run(
#         "src.api.v1.content_moderation:app",
#         host="0.0.0.0",
#         port=8999,
#         reload=settings.debug
#     )


# app/main.py (Updated with async job API)
"""
FastAPI application for content moderation service with async job processing.
"""
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from openai import OpenAI
from contextlib import asynccontextmanager
from typing import Optional
import tempfile

from src.utils.config import get_settings
from src.schemas.models import (
    TextModerationRequest,
    TextModerationResponse,
    ImageModerationRequest,
    ImageModerationResponse,
    VideoModerationResponse,
    KeyframeMethod,
    JobSubmitResponse,
    JobStatusResponse,
    QueueStatsResponse,
    JobProgressResponse
)
from src.services.text_moderation import TextModerationService
from src.services.image_moderation import ImageModerationService
from src.services.asr_service import ASRService
from src.services.video_moderation import VideoModerationService
from src.services.batch_processor import ImageBatchProcessor
from src.core.job_manager import job_manager, JobStatus
from src.core.queue_system import queue_system, Task, TaskType
from src.core.workers import WorkerPool
from src.utils.utils import (
    suppress_warnings,
    base64_to_image,
    download_image_from_url,
    validate_image
)


# Global service instances
text_service: TextModerationService = None
image_service: ImageModerationService = None
video_service: VideoModerationService = None
batch_processor: ImageBatchProcessor = None
worker_pool: WorkerPool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global text_service, image_service, video_service, batch_processor, worker_pool
    
    settings = get_settings()
    suppress_warnings()
    
    print("\n" + "="*70)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("="*70)
    print(f"📋 Configuration:")
    print(f"   Ollama Endpoint: {settings.ollama_base_url}")
    print(f"   Text Model: {settings.ollama_text_model}")
    print(f"   VLM Model: {settings.ollama_vlm_model}")
    print(f"   Device: {settings.device}")
    print(f"   Temp Directory: {settings.temp_dir}")
    print(f"   Save Keyframes: {settings.save_keyframes}")
    if settings.save_keyframes:
        print(f"   Keyframes Directory: {settings.keyframes_output_dir}")
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
    
    # Initialize batch processor
    batch_processor = ImageBatchProcessor(
        image_service=image_service,
        job_manager=job_manager,
        batch_size=8,
        batch_timeout=2.0
    )
    batch_processor.start()
    
    # Initialize and start worker pool
    worker_pool = WorkerPool(
        queue_system=queue_system,
        job_manager=job_manager,
        text_service=text_service,
        image_service=image_service,
        video_service=video_service,
        num_text_workers=settings.num_text_workers,
        num_image_workers=settings.num_image_workers,
        num_video_workers=settings.num_video_workers
    )
    worker_pool.start_all()
    
    print("="*70)
    print("✨ All services initialized successfully!")
    print("="*70 + "\n")
    
    yield
    
    print("\n🔴 Shutting down services...")
    batch_processor.stop()
    worker_pool.stop_all()



# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Content moderation API with async job processing",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "features": [
            "async_job_processing",
            "batch_image_moderation",
            "keyframe_detection",
            "queue_system"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "text_moderation": text_service is not None,
            "image_moderation": image_service is not None,
            "video_moderation": video_service is not None,
            "batch_processor": batch_processor is not None,
            "worker_pool": worker_pool is not None
        }
    }


@app.get("/stats")
async def get_stats():
    """Get queue statistics"""
    stats = queue_system.get_stats()
    return QueueStatsResponse(**stats)


# ============================================================================
# SYNC ENDPOINTS (Immediate response)
# ============================================================================

@app.post("/api/v1/moderate/text", response_model=TextModerationResponse)
async def moderate_text_sync(request: TextModerationRequest):
    """
    Moderate text content (synchronous).
    
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
async def moderate_image_sync(
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    image_base64: Optional[str] = Form(None)
):
    """
    Moderate image content (synchronous).
    
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
        
        if file:
            from PIL import Image
            import io
            image_bytes = await file.read()
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
                
        elif image_url:
            image = download_image_from_url(image_url)
            if not image:
                raise HTTPException(status_code=400, detail="Failed to download image from URL")
                
        elif image_base64:
            image = base64_to_image(image_base64)
            if not image:
                raise HTTPException(status_code=400, detail="Failed to decode base64 image")
        else:
            raise HTTPException(
                status_code=400,
                detail="No image provided. Please provide one of: file, image_url, or image_base64"
            )
        
        if not validate_image(image):
            raise HTTPException(status_code=400, detail="Invalid image format or size (max 4096x4096)")
        
        result = image_service.moderate(image)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image moderation failed: {str(e)}")


# ============================================================================
# ASYNC ENDPOINTS (Job-based)
# ============================================================================

@app.post("/api/v1/jobs/moderate/text", response_model=JobSubmitResponse)
async def moderate_text_async(request: TextModerationRequest):
    """
    Submit text moderation job (async).
    
    Returns job_id immediately, check status via /api/v1/jobs/{job_id}
    """
    try:
        job_id = job_manager.create_job("text", metadata={"text_length": len(request.text)})
        
        task = Task(
            job_id=job_id,
            task_type=TaskType.TEXT,
            data=request.text,
            priority=1
        )
        
        if not queue_system.submit_task(task):
            raise HTTPException(status_code=503, detail="Queue is full, please try again later")
        
        return JobSubmitResponse(
            job_id=job_id,
            status="pending",
            message="Text moderation job submitted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@app.post("/api/v1/jobs/moderate/image", response_model=JobSubmitResponse)
async def moderate_image_async(
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    image_base64: Optional[str] = Form(None),
    use_batch: bool = Form(False)
):
    """
    Submit image moderation job (async).
    
    Args:
        use_batch: Use batch processing for better throughput
        
    Returns job_id immediately
    """
    try:
        image = None
        
        if file:
            from PIL import Image
            import io
            image_bytes = await file.read()
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
                
        elif image_url:
            image = download_image_from_url(image_url)
            if not image:
                raise HTTPException(status_code=400, detail="Failed to download image from URL")
                
        elif image_base64:
            image = base64_to_image(image_base64)
            if not image:
                raise HTTPException(status_code=400, detail="Failed to decode base64 image")
        else:
            raise HTTPException(
                status_code=400,
                detail="No image provided"
            )
        
        if not validate_image(image):
            raise HTTPException(status_code=400, detail="Invalid image")
        
        job_id = job_manager.create_job("image", metadata={"use_batch": use_batch})
        
        if use_batch:
            # Submit to batch processor
            batch_processor.submit(job_id, image)
            message = "Image submitted to batch processor"
        else:
            # Submit to regular queue
            task = Task(
                job_id=job_id,
                task_type=TaskType.IMAGE,
                data=image,
                priority=1
            )
            
            if not queue_system.submit_task(task):
                raise HTTPException(status_code=503, detail="Queue is full")
            
            message = "Image moderation job submitted successfully"
        
        return JobSubmitResponse(
            job_id=job_id,
            status="pending",
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


# @app.post("/api/v1/jobs/moderate/video", response_model=JobSubmitResponse)
# async def moderate_video_async(
#     file: Optional[UploadFile] = File(None),
#     video_url: Optional[str] = Form(None),
#     sampling_fps: float = Form(0.5),
#     keyframe_method: KeyframeMethod = Form(KeyframeMethod.UNIFORM),
#     scene_detector_type: str = Form("content"),
#     scene_threshold: float = Form(27.0),
#     min_scene_length: float = Form(1.0)
# ):
#     """
#     Submit video moderation job (async).
    
#     Args:
#         use_keyframes: Use keyframe detection instead of uniform sampling
        
#     Returns job_id immediately
#     """
#     temp_video_path = None
    
#     try:
#         if file:
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
#                 temp_video_path = temp_file.name
#                 content = await file.read()
#                 temp_file.write(content)
                
#         elif video_url:
#             import requests
#             response = requests.get(video_url, timeout=30, stream=True)
#             response.raise_for_status()
            
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
#                 temp_video_path = temp_file.name
#                 for chunk in response.iter_content(chunk_size=8192):
#                     temp_file.write(chunk)
#         else:
#             raise HTTPException(status_code=400, detail="No video provided")
        
#         # job_id = job_manager.create_job(
#         #     "video",
#         #     metadata={
#         #         "sampling_fps": sampling_fps,
#         #         "use_keyframes": use_keyframes,
#         #         "video_path": temp_video_path
#         #     }
#         # )

#         job_id = job_manager.create_job(
#             "video",
#             metadata={
#                 "keyframe_method": keyframe_method.value,
#                 "sampling_fps": sampling_fps,
#                 "scene_detector_type": scene_detector_type,
#                 "scene_threshold": scene_threshold,
#                 "min_scene_length": min_scene_length,
#                 "video_path": temp_video_path
#             }
#         )
        
#         # task = Task(
#         #     job_id=job_id,
#         #     task_type=TaskType.VIDEO,
#         #     data=(temp_video_path, sampling_fps, use_keyframes),
#         #     priority=2  # Lower priority than text/image
#         # )

#         task = Task(
#             job_id=job_id,
#             task_type=TaskType.VIDEO,
#             data=(
#                 temp_video_path,
#                 sampling_fps,
#                 keyframe_method,
#                 scene_detector_type,
#                 scene_threshold,
#                 min_scene_length
#             ),
#             priority=2
#         )
        
#         # if not queue_system.submit_task(task):
#         #     if temp_video_path and os.path.exists(temp_video_path):
#         #         os.remove(temp_video_path)
#         #     raise HTTPException(status_code=503, detail="Queue is full")
        
#         # method = "keyframe detection" if use_keyframes else f"uniform sampling ({sampling_fps} fps)"
        
#         # return JobSubmitResponse(
#         #     job_id=job_id,
#         #     status="pending",
#         #     message=f"Video moderation job submitted successfully (method: {method})"
#         # )

#         if not queue_system.submit_task(task):
#             if temp_video_path and os.path.exists(temp_video_path):
#                 os.remove(temp_video_path)
#             raise HTTPException(status_code=503, detail="Queue is full")
        
#         method_display = {
#             KeyframeMethod.UNIFORM: f"uniform sampling ({sampling_fps} fps)",
#             KeyframeMethod.DIFFERENCE: "frame difference analysis",
#             KeyframeMethod.SCENE: f"scene detection ({scene_detector_type})"
#         }
        
#         return JobSubmitResponse(
#             job_id=job_id,
#             status="pending",
#             message=f"Video moderation job submitted successfully (method: {method_display[keyframe_method]})"
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         if temp_video_path and os.path.exists(temp_video_path):
#             try:
#                 os.remove(temp_video_path)
#             except:
#                 pass
#         raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


# @app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse)
# async def get_job_status(job_id: str):
#     """
#     Get job status and result.
    
#     Args:
#         job_id: Job ID returned from submission
        
#     Returns:
#         Job status, progress, and result if completed
#     """
#     job = job_manager.get_job(job_id)
    
#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")
    
#     progress = None
#     if job.progress.total > 0:
#         progress = JobProgressResponse(
#             processed=job.progress.processed,
#             total=job.progress.total,
#             percentage=job.progress.percentage
#         )
    
#     return JobStatusResponse(
#         job_id=job.job_id,
#         job_type=job.job_type,
#         status=job.status.value,
#         created_at=job.created_at,
#         started_at=job.started_at,
#         completed_at=job.completed_at,
#         progress=progress,
#         result=job.result,
#         error=job.error
#     )


# @app.delete("/api/v1/jobs/{job_id}")
# async def cancel_job(job_id: str):
#     """
#     Cancel a pending job.
    
#     Note: Cannot cancel jobs that are already processing
#     """
#     job = job_manager.get_job(job_id)
    
#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")
    
#     if job.status == JobStatus.PENDING:
#         job_manager.update_status(job_id, JobStatus.CANCELLED)
#         return {"message": "Job cancelled successfully"}
#     elif job.status == JobStatus.PROCESSING:
#         raise HTTPException(status_code=400, detail="Cannot cancel job that is already processing")
#     else:
#         raise HTTPException(status_code=400, detail=f"Job is already {job.status.value}")



@app.post("/api/v1/jobs/moderate/video", response_model=JobSubmitResponse)
async def moderate_video_async(
    file: Optional[UploadFile] = File(None),
    video_url: Optional[str] = Form(None),
    sampling_fps: float = Form(0.5),
    keyframe_method: KeyframeMethod = Form(KeyframeMethod.UNIFORM),
    scene_detector_type: str = Form("content"),
    scene_threshold: float = Form(27.0),
    min_scene_length: float = Form(1.0)
):
    """
    Submit video moderation job (async).
    
    Args:
        file: Video file upload
        video_url: URL to video file
        sampling_fps: Frame sampling rate (for uniform method)
        keyframe_method: Frame selection strategy
            - "uniform": Uniform sampling at sampling_fps
            - "difference": Frame difference analysis (adaptive)
            - "scene": Scene detection using PySceneDetect
        scene_detector_type: "content" or "adaptive" (for scene method)
        scene_threshold: Scene detection sensitivity (for scene method)
            - ContentDetector: 15-35 (lower = more sensitive)
            - AdaptiveDetector: 2-5
        min_scene_length: Minimum scene length in seconds (for scene method)
        
    Returns:
        Job submission response with job_id
    """
    temp_video_path = None
    
    try:
        # Handle file upload or URL
        if file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_video_path = temp_file.name
                content = await file.read()
                temp_file.write(content)
                
        elif video_url:
            import requests
            response = requests.get(video_url, timeout=30, stream=True)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_video_path = temp_file.name
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
        else:
            raise HTTPException(status_code=400, detail="No video provided")
        
        # Create job
        job_id = job_manager.create_job(
            "video",
            metadata={
                "keyframe_method": keyframe_method.value,
                "sampling_fps": sampling_fps,
                "scene_detector_type": scene_detector_type,
                "scene_threshold": scene_threshold,
                "min_scene_length": min_scene_length,
                "video_path": temp_video_path
            }
        )
        
        # Create task with all parameters
        task = Task(
            job_id=job_id,
            task_type=TaskType.VIDEO,
            data=(
                temp_video_path,
                sampling_fps,
                keyframe_method,
                scene_detector_type,
                scene_threshold,
                min_scene_length
            ),
            priority=2
        )
        
        # Submit to queue
        if not queue_system.submit_task(task):
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            raise HTTPException(status_code=503, detail="Queue is full")
        
        # Build response message
        method_display = {
            KeyframeMethod.UNIFORM: f"uniform sampling ({sampling_fps} fps)",
            KeyframeMethod.DIFFERENCE: "frame difference analysis (adaptive)",
            KeyframeMethod.SCENE: f"scene detection ({scene_detector_type}, threshold={scene_threshold})"
        }
        
        return JobSubmitResponse(
            job_id=job_id,
            status="pending",
            message=f"Video moderation job submitted successfully. Method: {method_display[keyframe_method]}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get job status and result.
    
    Args:
        job_id: Job ID returned from submission
        
    Returns:
        Job status, progress, and result if completed
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    progress = None
    if job.progress.total > 0:
        progress = JobProgressResponse(
            processed=job.progress.processed,
            total=job.progress.total,
            percentage=job.progress.percentage
        )
    
    return JobStatusResponse(
        job_id=job.job_id,
        job_type=job.job_type,
        status=job.status.value,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        progress=progress,
        result=job.result,
        error=job.error
    )


@app.delete("/api/v1/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a pending job"""
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == JobStatus.PENDING:
        job_manager.update_status(job_id, JobStatus.CANCELLED)
        return {"message": "Job cancelled successfully"}
    elif job.status == JobStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Cannot cancel job that is already processing")
    else:
        raise HTTPException(status_code=400, detail=f"Job is already {job.status.value}")


@app.get("/stats/workers")
async def get_worker_stats():
    """Get worker pool statistics"""
    if worker_pool:
        return worker_pool.get_stats()
    return {"error": "Worker pool not initialized"}


@app.get("/stats/queue")
async def get_queue_stats():
    """Get queue statistics"""
    stats = queue_system.get_stats()
    return stats


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