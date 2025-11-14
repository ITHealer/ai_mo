import os
import tempfile
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    app_name: str = "Content Moderation API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Ollama Settings
    ollama_base_url: str = os.getenv("OLLAMA_ENDPOINT", "http://10.10.0.7:11445")
    ollama_text_model: str = os.getenv("OLLAMA_TEXT_MODEL", "gpt-oss:20b")
    ollama_vlm_model: str = os.getenv("OLLAMA_VLM_MODEL", "gemma3:12b")
    
    # Model Settings
    whisper_model_id: str = "openai/whisper-base"
    device: str = "cuda"  # or "cpu"
    
    # Video Processing Settings
    default_video_sampling_fps: float = 0.5
    max_video_duration_seconds: int = 300  # 5 minutes

    # Keyframe Settings
    save_keyframes: bool = os.getenv("SAVE_KEYFRAMES", "false").lower() == "true"
    keyframes_output_dir: str = os.getenv("KEYFRAMES_DIR", "./output/keyframes")
    keyframes_organize_by_category: bool = os.getenv("KEYFRAMES_ORGANIZE_BY_CATEGORY", "true").lower() == "true"
    keyframes_include_safe: bool = os.getenv("KEYFRAMES_INCLUDE_SAFE", "true").lower() == "true"
    

    # Temp Files
    temp_dir: str = tempfile.gettempdir()

    # Worker Settings
    num_text_workers: int = int(os.getenv("TEXT_WORKERS", "4"))
    num_image_workers: int = int(os.getenv("IMAGE_WORKERS", "8"))
    num_video_workers: int = int(os.getenv("VIDEO_WORKERS", "2"))

    # Logging Settings
    log_worker_activity: bool = True
    log_progress_interval: int = 5  # Log progress every N frames
    
    def get_temp_audio_path(self) -> str:
        """Get temporary audio file path"""
        return os.path.join(self.temp_dir, "temp_audio.wav")
    
    def ensure_keyframes_dir(self) -> str:
        """Ensure keyframes directory exists"""
        if self.save_keyframes:
            os.makedirs(self.keyframes_output_dir, exist_ok=True)
        return self.keyframes_output_dir
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # class Config:
    #     env_file = ".env"
    #     case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()