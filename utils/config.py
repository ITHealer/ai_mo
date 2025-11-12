import os
import tempfile
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    
    # Temp Files
    temp_dir: str = tempfile.gettempdir()
    
    def get_temp_audio_path(self) -> str:
        """Get temporary audio file path"""
        return os.path.join(self.temp_dir, "temp_audio.wav")
    
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