import os
import cv2
from PIL import Image
from pathlib import Path
from typing import List, Dict, Optional
from moviepy.editor import VideoFileClip

from src.schemas.models import (
    ModerationCategory,
    CATEGORY_DISPLAY_NAMES,
    TextModerationResponse,
    FrameModerationResult,
    VideoModerationSummary,
    VideoModerationResponse,
    ImageAnalysis
)
from src.services.text_moderation import TextModerationService
from src.services.image_moderation import ImageModerationService
from src.services.asr_service import ASRService


class VideoModerationService:
    """Service for moderating video content"""
    
    def __init__(
        self,
        text_service: TextModerationService,
        image_service: ImageModerationService,
        asr_service: ASRService
    ):
        """
        Initialize video moderation service.
        
        Args:
            text_service: Text moderation service instance
            image_service: Image moderation service instance
            asr_service: ASR service instance
        """
        self.text_service = text_service
        self.image_service = image_service
        self.asr_service = asr_service
        print("✅ VideoModerationService initialized")
    
    def moderate(
        self,
        video_path: str,
        sampling_fps: float = 0.5
    ) -> VideoModerationResponse:
        """
        Moderate video content (audio + frames).
        
        Args:
            video_path: Path to video file
            sampling_fps: Frame sampling rate (frames per second)
            
        Returns:
            VideoModerationResponse with comprehensive analysis
        """
        print(f"\n{'='*70}")
        print(f"🎥 VIDEO MODERATION: {Path(video_path).name}")
        print(f"{'='*70}")
        
        if not video_path or not os.path.exists(video_path):
            return self._create_error_response("Video file not found")
        
        # Moderate audio
        audio_result = self._moderate_audio(video_path)
        
        # Moderate frames
        frame_results = self._moderate_frames(video_path, sampling_fps)
        
        # Aggregate results
        response = self._aggregate_results(audio_result, frame_results)
        
        print(f"{'='*70}")
        print(f"✅ RESULT: {response.overall_decision} ({response.overall_confidence:.0%})")
        print(f"{'='*70}\n")
        
        return response
    
    def _moderate_audio(self, video_path: str) -> TextModerationResponse:
        """Extract and moderate audio from video"""
        print("🔊 Processing audio...")
        
        temp_audio_path = None
        try:
            temp_audio_path = self._extract_audio(video_path)
            
            if not temp_audio_path:
                return TextModerationResponse(
                    category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
                    category_code=ModerationCategory.SAFE.value,
                    confidence=1.0,
                    reasoning="No audio track"
                )
            
            transcript = self.asr_service.transcribe(temp_audio_path)
            
            if not transcript:
                return TextModerationResponse(
                    category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
                    category_code=ModerationCategory.SAFE.value,
                    confidence=1.0,
                    reasoning="No speech detected"
                )
            
            return self.text_service.moderate(transcript)
            
        except Exception as e:
            print(f"   ⚠️  Audio moderation error: {e}")
            return TextModerationResponse(
                category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
                category_code=ModerationCategory.SAFE.value,
                confidence=0.5,
                reasoning=f"Audio processing error: {str(e)[:50]}"
            )
        finally:
            # Clean up temp audio file
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception as e:
                    print(f"   ⚠️  Failed to remove temp audio: {e}")
    
    def _moderate_frames(
        self,
        video_path: str,
        sampling_fps: float
    ) -> List[FrameModerationResult]:
        """Extract and moderate video frames"""
        print(f"🎞️  Processing frames (sampling @ {sampling_fps} fps)...")
        
        frames = self._extract_frames(video_path, sampling_fps)
        results = []
        
        for i, frame_data in enumerate(frames):
            timestamp = frame_data["timestamp_sec"]
            image = frame_data["image"]
            
            print(f"   Frame {i+1}/{len(frames)} @ {timestamp:.1f}s", end=" ")
            
            moderation_result = self.image_service.moderate(image)
            
            frame_result = FrameModerationResult(
                timestamp=timestamp,
                frame_index=i,
                category=moderation_result.category,
                category_code=moderation_result.category_code,
                confidence=moderation_result.confidence,
                reasoning=moderation_result.reasoning,
                analysis=moderation_result.analysis
            )
            
            results.append(frame_result)
            print(f"✓ {moderation_result.category}")
        
        return results
    
    def _aggregate_results(
        self,
        audio_result: TextModerationResponse,
        frame_results: List[FrameModerationResult]
    ) -> VideoModerationResponse:
        """Aggregate audio and frame moderation results"""
        
        overall_decision = CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE]
        overall_decision_code = ModerationCategory.SAFE.value
        overall_confidence = 1.0
        flagged_content = []
        
        # Check audio
        if audio_result.category_code != ModerationCategory.SAFE.value:
            overall_decision = audio_result.category
            overall_decision_code = audio_result.category_code
            overall_confidence = audio_result.confidence
            flagged_content.append(f"🔊 Audio: {audio_result.category}")
        
        # Check frames
        flagged_categories = {}
        for frame in frame_results:
            if frame.category_code != ModerationCategory.SAFE.value:
                if frame.category_code not in flagged_categories:
                    flagged_categories[frame.category_code] = []
                flagged_categories[frame.category_code].append(frame.timestamp)
        
        # Aggregate flagged frames
        for cat_code, timestamps in flagged_categories.items():
            cat_display = CATEGORY_DISPLAY_NAMES[ModerationCategory(cat_code)]
            flagged_content.append(
                f"🎞️  {cat_display}: {len(timestamps)} frames"
            )
            
            # Update overall decision if audio is safe
            if overall_decision_code == ModerationCategory.SAFE.value:
                overall_decision = cat_display
                overall_decision_code = cat_code
                
                # Calculate average confidence of flagged frames
                flagged_frames = [
                    f for f in frame_results
                    if f.category_code == cat_code
                ]
                avg_conf = sum(f.confidence for f in flagged_frames) / len(flagged_frames)
                overall_confidence = round(avg_conf, 2)
        
        # Calculate summary
        total_frames = len(frame_results)
        flagged_frames_count = sum(
            1 for f in frame_results
            if f.category_code != ModerationCategory.SAFE.value
        )
        
        summary = VideoModerationSummary(
            total_frames=total_frames,
            flagged_frames=flagged_frames_count,
            flagged_percentage=round(
                (flagged_frames_count / total_frames * 100) if total_frames > 0 else 0,
                1
            ),
            audio_safe=(audio_result.category_code == ModerationCategory.SAFE.value)
        )
        
        return VideoModerationResponse(
            overall_decision=overall_decision,
            overall_decision_code=overall_decision_code,
            overall_confidence=overall_confidence,
            flagged_content=flagged_content,
            audio_moderation=audio_result,
            frame_moderation=frame_results,
            summary=summary
        )
    
    def _extract_audio(self, video_path: str) -> Optional[str]:
        """Extract audio track from video"""
        clip = None
        temp_audio_path = None
        
        try:
            clip = VideoFileClip(video_path)
            
            # Check if video has audio
            if clip.audio is None:
                print("   ℹ️  No audio track found")
                return None
            
            # Create temporary file with proper extension
            temp_audio_fd, temp_audio_path = tempfile.mkstemp(suffix='.wav', prefix='audio_')
            os.close(temp_audio_fd)  # Close file descriptor
            
            # Write audio to temp file
            clip.audio.write_audiofile(
                temp_audio_path,
                codec='pcm_s16le',
                logger=None,
                verbose=False,
                fps=16000
            )
            
            print(f"   ✅ Audio extracted: {temp_audio_path}")
            return temp_audio_path
            
        except Exception as e:
            print(f"   Audio extraction error: {e}")
            # Clean up on error
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except:
                    pass
            return None
        finally:
            # Always close the video clip
            if clip:
                try:
                    clip.close()
                except:
                    pass
    
    def _extract_frames(
        self,
        video_path: str,
        sampling_fps: float
    ) -> List[Dict]:
        """Extract frames from video at specified sampling rate"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("   ❌ Failed to open video file")
            return []
        
        frames = []
        frame_count = 0
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
        interval = max(1, int(video_fps / sampling_fps))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % interval == 0:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                
                frames.append({
                    "timestamp_sec": timestamp,
                    "image": pil_image
                })
            
            frame_count += 1
        
        cap.release()
        print(f"   ✅ Extracted {len(frames)} frames")
        return frames
    
    def _create_error_response(self, error_message: str) -> VideoModerationResponse:
        """Create error response"""
        return VideoModerationResponse(
            overall_decision="Error",
            overall_decision_code="error",
            overall_confidence=0.0,
            flagged_content=[error_message],
            audio_moderation=TextModerationResponse(
                category="Error",
                category_code="error",
                confidence=0.0,
                reasoning=error_message
            ),
            frame_moderation=[],
            summary=VideoModerationSummary(
                total_frames=0,
                flagged_frames=0,
                flagged_percentage=0.0,
                audio_safe=False
            )
        )