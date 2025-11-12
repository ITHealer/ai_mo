import torch
import librosa
import transformers
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from typing import Optional


class ASRService:
    """Service for audio transcription"""
    
    def __init__(self, model_id: str = "openai/whisper-base", device: str = "cuda"):
        """
        Initialize ASR service.
        
        Args:
            model_id: Hugging Face model ID for Whisper
            device: Device to use (cuda/cpu)
        """
        self.device = device if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        
        print(f"Loading Whisper ASR: {model_id} on {self.device}...")
        
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=self.torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True
        ).to(self.device)
        
        self.pipeline = transformers.pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=16,
            torch_dtype=self.torch_dtype,
            device=self.device,
        )
        
        print("ASR Service initialized")
    
    def transcribe(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text or None if error
        """
        try:
            speech_array, _ = librosa.load(audio_path, sr=16000)
            result = self.pipeline(speech_array)
            return result["text"]
        except Exception as e:
            print(f"ASR transcription error: {e}")
            return None