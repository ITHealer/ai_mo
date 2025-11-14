# # # import os
# # # import cv2
# # # from PIL import Image
# # # from pathlib import Path
# # # from typing import List, Dict, Optional
# # # from moviepy.editor import VideoFileClip

# # # from src.schemas.models import (
# # #     ModerationCategory,
# # #     CATEGORY_DISPLAY_NAMES,
# # #     TextModerationResponse,
# # #     FrameModerationResult,
# # #     VideoModerationSummary,
# # #     VideoModerationResponse,
# # #     ImageAnalysis
# # # )
# # # from src.services.text_moderation import TextModerationService
# # # from src.services.image_moderation import ImageModerationService
# # # from src.services.asr_service import ASRService


# # # class VideoModerationService:
# # #     """Service for moderating video content"""
    
# # #     def __init__(
# # #         self,
# # #         text_service: TextModerationService,
# # #         image_service: ImageModerationService,
# # #         asr_service: ASRService
# # #     ):
# # #         """
# # #         Initialize video moderation service.
        
# # #         Args:
# # #             text_service: Text moderation service instance
# # #             image_service: Image moderation service instance
# # #             asr_service: ASR service instance
# # #         """
# # #         self.text_service = text_service
# # #         self.image_service = image_service
# # #         self.asr_service = asr_service
# # #         print("✅ VideoModerationService initialized")
    
# # #     def moderate(
# # #         self,
# # #         video_path: str,
# # #         sampling_fps: float = 0.5
# # #     ) -> VideoModerationResponse:
# # #         """
# # #         Moderate video content (audio + frames).
        
# # #         Args:
# # #             video_path: Path to video file
# # #             sampling_fps: Frame sampling rate (frames per second)
            
# # #         Returns:
# # #             VideoModerationResponse with comprehensive analysis
# # #         """
# # #         print(f"\n{'='*70}")
# # #         print(f"🎥 VIDEO MODERATION: {Path(video_path).name}")
# # #         print(f"{'='*70}")
        
# # #         if not video_path or not os.path.exists(video_path):
# # #             return self._create_error_response("Video file not found")
        
# # #         # Moderate audio
# # #         audio_result = self._moderate_audio(video_path)
        
# # #         # Moderate frames
# # #         frame_results = self._moderate_frames(video_path, sampling_fps)
        
# # #         # Aggregate results
# # #         response = self._aggregate_results(audio_result, frame_results)
        
# # #         print(f"{'='*70}")
# # #         print(f"✅ RESULT: {response.overall_decision} ({response.overall_confidence:.0%})")
# # #         print(f"{'='*70}\n")
        
# # #         return response
    
# # #     def _moderate_audio(self, video_path: str) -> TextModerationResponse:
# # #         """Extract and moderate audio from video"""
# # #         print("🔊 Processing audio...")
        
# # #         temp_audio_path = None
# # #         try:
# # #             temp_audio_path = self._extract_audio(video_path)
            
# # #             if not temp_audio_path:
# # #                 return TextModerationResponse(
# # #                     category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
# # #                     category_code=ModerationCategory.SAFE.value,
# # #                     confidence=1.0,
# # #                     reasoning="No audio track"
# # #                 )
            
# # #             transcript = self.asr_service.transcribe(temp_audio_path)
            
# # #             if not transcript:
# # #                 return TextModerationResponse(
# # #                     category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
# # #                     category_code=ModerationCategory.SAFE.value,
# # #                     confidence=1.0,
# # #                     reasoning="No speech detected"
# # #                 )
            
# # #             return self.text_service.moderate(transcript)
            
# # #         except Exception as e:
# # #             print(f"   ⚠️  Audio moderation error: {e}")
# # #             return TextModerationResponse(
# # #                 category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
# # #                 category_code=ModerationCategory.SAFE.value,
# # #                 confidence=0.5,
# # #                 reasoning=f"Audio processing error: {str(e)[:50]}"
# # #             )
# # #         finally:
# # #             # Clean up temp audio file
# # #             if temp_audio_path and os.path.exists(temp_audio_path):
# # #                 try:
# # #                     os.remove(temp_audio_path)
# # #                 except Exception as e:
# # #                     print(f"   ⚠️  Failed to remove temp audio: {e}")
    
# # #     def _moderate_frames(
# # #         self,
# # #         video_path: str,
# # #         sampling_fps: float
# # #     ) -> List[FrameModerationResult]:
# # #         """Extract and moderate video frames"""
# # #         print(f"🎞️  Processing frames (sampling @ {sampling_fps} fps)...")
        
# # #         frames = self._extract_frames(video_path, sampling_fps)
# # #         results = []
        
# # #         for i, frame_data in enumerate(frames):
# # #             timestamp = frame_data["timestamp_sec"]
# # #             image = frame_data["image"]
            
# # #             print(f"   Frame {i+1}/{len(frames)} @ {timestamp:.1f}s", end=" ")
            
# # #             moderation_result = self.image_service.moderate(image)
            
# # #             frame_result = FrameModerationResult(
# # #                 timestamp=timestamp,
# # #                 frame_index=i,
# # #                 category=moderation_result.category,
# # #                 category_code=moderation_result.category_code,
# # #                 confidence=moderation_result.confidence,
# # #                 reasoning=moderation_result.reasoning,
# # #                 analysis=moderation_result.analysis
# # #             )
            
# # #             results.append(frame_result)
# # #             print(f"✓ {moderation_result.category}")
        
# # #         return results
    
# # #     def _aggregate_results(
# # #         self,
# # #         audio_result: TextModerationResponse,
# # #         frame_results: List[FrameModerationResult]
# # #     ) -> VideoModerationResponse:
# # #         """Aggregate audio and frame moderation results"""
        
# # #         overall_decision = CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE]
# # #         overall_decision_code = ModerationCategory.SAFE.value
# # #         overall_confidence = 1.0
# # #         flagged_content = []
        
# # #         # Check audio
# # #         if audio_result.category_code != ModerationCategory.SAFE.value:
# # #             overall_decision = audio_result.category
# # #             overall_decision_code = audio_result.category_code
# # #             overall_confidence = audio_result.confidence
# # #             flagged_content.append(f"🔊 Audio: {audio_result.category}")
        
# # #         # Check frames
# # #         flagged_categories = {}
# # #         for frame in frame_results:
# # #             if frame.category_code != ModerationCategory.SAFE.value:
# # #                 if frame.category_code not in flagged_categories:
# # #                     flagged_categories[frame.category_code] = []
# # #                 flagged_categories[frame.category_code].append(frame.timestamp)
        
# # #         # Aggregate flagged frames
# # #         for cat_code, timestamps in flagged_categories.items():
# # #             cat_display = CATEGORY_DISPLAY_NAMES[ModerationCategory(cat_code)]
# # #             flagged_content.append(
# # #                 f"🎞️  {cat_display}: {len(timestamps)} frames"
# # #             )
            
# # #             # Update overall decision if audio is safe
# # #             if overall_decision_code == ModerationCategory.SAFE.value:
# # #                 overall_decision = cat_display
# # #                 overall_decision_code = cat_code
                
# # #                 # Calculate average confidence of flagged frames
# # #                 flagged_frames = [
# # #                     f for f in frame_results
# # #                     if f.category_code == cat_code
# # #                 ]
# # #                 avg_conf = sum(f.confidence for f in flagged_frames) / len(flagged_frames)
# # #                 overall_confidence = round(avg_conf, 2)
        
# # #         # Calculate summary
# # #         total_frames = len(frame_results)
# # #         flagged_frames_count = sum(
# # #             1 for f in frame_results
# # #             if f.category_code != ModerationCategory.SAFE.value
# # #         )
        
# # #         summary = VideoModerationSummary(
# # #             total_frames=total_frames,
# # #             flagged_frames=flagged_frames_count,
# # #             flagged_percentage=round(
# # #                 (flagged_frames_count / total_frames * 100) if total_frames > 0 else 0,
# # #                 1
# # #             ),
# # #             audio_safe=(audio_result.category_code == ModerationCategory.SAFE.value)
# # #         )
        
# # #         return VideoModerationResponse(
# # #             overall_decision=overall_decision,
# # #             overall_decision_code=overall_decision_code,
# # #             overall_confidence=overall_confidence,
# # #             flagged_content=flagged_content,
# # #             audio_moderation=audio_result,
# # #             frame_moderation=frame_results,
# # #             summary=summary
# # #         )
    
# # #     def _extract_audio(self, video_path: str) -> Optional[str]:
# # #         """Extract audio track from video"""
# # #         clip = None
# # #         temp_audio_path = None
        
# # #         try:
# # #             clip = VideoFileClip(video_path)
            
# # #             # Check if video has audio
# # #             if clip.audio is None:
# # #                 print("   ℹ️  No audio track found")
# # #                 return None
            
# # #             # Create temporary file with proper extension
# # #             temp_audio_fd, temp_audio_path = tempfile.mkstemp(suffix='.wav', prefix='audio_')
# # #             os.close(temp_audio_fd)  # Close file descriptor
            
# # #             # Write audio to temp file
# # #             clip.audio.write_audiofile(
# # #                 temp_audio_path,
# # #                 codec='pcm_s16le',
# # #                 logger=None,
# # #                 verbose=False,
# # #                 fps=16000
# # #             )
            
# # #             print(f"   ✅ Audio extracted: {temp_audio_path}")
# # #             return temp_audio_path
            
# # #         except Exception as e:
# # #             print(f"   Audio extraction error: {e}")
# # #             # Clean up on error
# # #             if temp_audio_path and os.path.exists(temp_audio_path):
# # #                 try:
# # #                     os.remove(temp_audio_path)
# # #                 except:
# # #                     pass
# # #             return None
# # #         finally:
# # #             # Always close the video clip
# # #             if clip:
# # #                 try:
# # #                     clip.close()
# # #                 except:
# # #                     pass
    
# # #     def _extract_frames(
# # #         self,
# # #         video_path: str,
# # #         sampling_fps: float
# # #     ) -> List[Dict]:
# # #         """Extract frames from video at specified sampling rate"""
# # #         cap = cv2.VideoCapture(video_path)
# # #         if not cap.isOpened():
# # #             print("   ❌ Failed to open video file")
# # #             return []
        
# # #         frames = []
# # #         frame_count = 0
# # #         video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
# # #         interval = max(1, int(video_fps / sampling_fps))
        
# # #         while True:
# # #             ret, frame = cap.read()
# # #             if not ret:
# # #                 break
            
# # #             if frame_count % interval == 0:
# # #                 rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
# # #                 pil_image = Image.fromarray(rgb_frame)
# # #                 timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                
# # #                 frames.append({
# # #                     "timestamp_sec": timestamp,
# # #                     "image": pil_image
# # #                 })
            
# # #             frame_count += 1
        
# # #         cap.release()
# # #         print(f"   ✅ Extracted {len(frames)} frames")
# # #         return frames
    
# # #     def _create_error_response(self, error_message: str) -> VideoModerationResponse:
# # #         """Create error response"""
# # #         return VideoModerationResponse(
# # #             overall_decision="Error",
# # #             overall_decision_code="error",
# # #             overall_confidence=0.0,
# # #             flagged_content=[error_message],
# # #             audio_moderation=TextModerationResponse(
# # #                 category="Error",
# # #                 category_code="error",
# # #                 confidence=0.0,
# # #                 reasoning=error_message
# # #             ),
# # #             frame_moderation=[],
# # #             summary=VideoModerationSummary(
# # #                 total_frames=0,
# # #                 flagged_frames=0,
# # #                 flagged_percentage=0.0,
# # #                 audio_safe=False
# # #             )
# # #         )

# # # app/services/video_moderation.py (Updated with progress callback and keyframe)
# # """
# # Video content moderation service.
# # """
# # import os
# # import cv2
# # import tempfile
# # from pathlib import Path
# # from PIL import Image
# # from typing import List, Dict, Optional, Callable
# # from moviepy.editor import VideoFileClip

# # from src.schemas.models import (
# #     ModerationCategory,
# #     CATEGORY_DISPLAY_NAMES,
# #     TextModerationResponse,
# #     FrameModerationResult,
# #     VideoModerationSummary,
# #     VideoModerationResponse,
# #     ImageAnalysis
# # )
# # from src.services.text_moderation import TextModerationService
# # from src.services.image_moderation import ImageModerationService
# # from src.services.asr_service import ASRService
# # from src.services.keyframe_detector import KeyframeDetector


# # class VideoModerationService:
# #     """Service for moderating video content"""
    
# #     def __init__(
# #         self,
# #         text_service: TextModerationService,
# #         image_service: ImageModerationService,
# #         asr_service: ASRService
# #     ):
# #         """
# #         Initialize video moderation service.
        
# #         Args:
# #             text_service: Text moderation service instance
# #             image_service: Image moderation service instance
# #             asr_service: ASR service instance
# #         """
# #         self.text_service = text_service
# #         self.image_service = image_service
# #         self.asr_service = asr_service
# #         self.keyframe_detector = KeyframeDetector(threshold=0.3, max_keyframes=8)
# #         print("✅ VideoModerationService initialized")
    
# #     def moderate(
# #         self,
# #         video_path: str,
# #         sampling_fps: float = 0.5,
# #         progress_callback: Optional[Callable[[int, int], None]] = None,
# #         use_keyframes: bool = False
# #     ) -> VideoModerationResponse:
# #         """
# #         Moderate video content (audio + frames).
        
# #         Args:
# #             video_path: Path to video file
# #             sampling_fps: Frame sampling rate (frames per second)
# #             progress_callback: Optional callback for progress updates (processed, total)
# #             use_keyframes: Use keyframe detection instead of uniform sampling
            
# #         Returns:
# #             VideoModerationResponse with comprehensive analysis
# #         """
# #         print(f"\n{'='*70}")
# #         print(f"🎥 VIDEO MODERATION: {Path(video_path).name}")
# #         print(f"{'='*70}")
        
# #         if not video_path or not os.path.exists(video_path):
# #             return self._create_error_response("Video file not found")
        
# #         # Moderate audio
# #         audio_result = self._moderate_audio(video_path)
        
# #         # Moderate frames (keyframe or uniform sampling)
# #         if use_keyframes:
# #             frame_results = self._moderate_keyframes(video_path, progress_callback)
# #         else:
# #             frame_results = self._moderate_frames(video_path, sampling_fps, progress_callback)
        
# #         # Aggregate results
# #         response = self._aggregate_results(audio_result, frame_results)
        
# #         print(f"{'='*70}")
# #         print(f"✅ RESULT: {response.overall_decision} ({response.overall_confidence:.0%})")
# #         print(f"{'='*70}\n")
        
# #         return response
    
# #     def _moderate_keyframes(
# #         self,
# #         video_path: str,
# #         progress_callback: Optional[Callable] = None
# #     ) -> List[FrameModerationResult]:
# #         """Moderate video using keyframe detection"""
# #         print("🔑 Using keyframe detection...")
        
# #         try:
# #             keyframes = self.keyframe_detector.detect(video_path)
            
# #             if not keyframes:
# #                 print("⚠️  No keyframes detected, falling back to uniform sampling")
# #                 return self._moderate_frames(video_path, 0.5, progress_callback)
            
# #             results = []
# #             total_frames = len(keyframes)
            
# #             for i, keyframe_data in enumerate(keyframes):
# #                 timestamp = keyframe_data["timestamp"]
# #                 image = keyframe_data["image"]
# #                 frame_idx = keyframe_data["frame_index"]
                
# #                 print(f"   Keyframe {i+1}/{total_frames} @ {timestamp:.1f}s", end=" ")
                
# #                 moderation_result = self.image_service.moderate(image)
                
# #                 frame_result = FrameModerationResult(
# #                     timestamp=timestamp,
# #                     frame_index=frame_idx,
# #                     category=moderation_result.category,
# #                     category_code=moderation_result.category_code,
# #                     confidence=moderation_result.confidence,
# #                     reasoning=moderation_result.reasoning,
# #                     analysis=moderation_result.analysis
# #                 )
                
# #                 results.append(frame_result)
# #                 print(f"✓ {moderation_result.category}")
                
# #                 # Progress callback
# #                 if progress_callback:
# #                     progress_callback(i + 1, total_frames)
            
# #             return results
            
# #         except Exception as e:
# #             print(f"❌ Keyframe detection failed: {e}")
# #             return self._moderate_frames(video_path, 0.5, progress_callback)
    
# #     def _moderate_audio(self, video_path: str) -> TextModerationResponse:
# #         """Extract and moderate audio from video"""
# #         print("🔊 Processing audio...")
        
# #         temp_audio_path = None
# #         try:
# #             temp_audio_path = self._extract_audio(video_path)
            
# #             if not temp_audio_path:
# #                 return TextModerationResponse(
# #                     category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
# #                     category_code=ModerationCategory.SAFE.value,
# #                     confidence=1.0,
# #                     reasoning="No audio track"
# #                 )
            
# #             transcript = self.asr_service.transcribe(temp_audio_path)
            
# #             if not transcript:
# #                 return TextModerationResponse(
# #                     category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
# #                     category_code=ModerationCategory.SAFE.value,
# #                     confidence=1.0,
# #                     reasoning="No speech detected"
# #                 )
            
# #             return self.text_service.moderate(transcript)
            
# #         except Exception as e:
# #             print(f"   ⚠️  Audio moderation error: {e}")
# #             return TextModerationResponse(
# #                 category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
# #                 category_code=ModerationCategory.SAFE.value,
# #                 confidence=0.5,
# #                 reasoning=f"Audio processing error: {str(e)[:50]}"
# #             )
# #         finally:
# #             if temp_audio_path and os.path.exists(temp_audio_path):
# #                 try:
# #                     os.remove(temp_audio_path)
# #                 except Exception as e:
# #                     print(f"   ⚠️  Failed to remove temp audio: {e}")
    
# #     def _moderate_frames(
# #         self,
# #         video_path: str,
# #         sampling_fps: float,
# #         progress_callback: Optional[Callable] = None
# #     ) -> List[FrameModerationResult]:
# #         """Extract and moderate video frames"""
# #         print(f"🎞️  Processing frames (sampling @ {sampling_fps} fps)...")
        
# #         frames = self._extract_frames(video_path, sampling_fps)
# #         results = []
# #         total_frames = len(frames)
        
# #         for i, frame_data in enumerate(frames):
# #             timestamp = frame_data["timestamp_sec"]
# #             image = frame_data["image"]
            
# #             print(f"   Frame {i+1}/{total_frames} @ {timestamp:.1f}s", end=" ")
            
# #             moderation_result = self.image_service.moderate(image)
            
# #             frame_result = FrameModerationResult(
# #                 timestamp=timestamp,
# #                 frame_index=i,
# #                 category=moderation_result.category,
# #                 category_code=moderation_result.category_code,
# #                 confidence=moderation_result.confidence,
# #                 reasoning=moderation_result.reasoning,
# #                 analysis=moderation_result.analysis
# #             )
            
# #             results.append(frame_result)
# #             print(f"✓ {moderation_result.category}")
            
# #             # Progress callback
# #             if progress_callback:
# #                 progress_callback(i + 1, total_frames)
        
# #         return results
    
# #     def _aggregate_results(
# #         self,
# #         audio_result: TextModerationResponse,
# #         frame_results: List[FrameModerationResult]
# #     ) -> VideoModerationResponse:
# #         """Aggregate audio and frame moderation results"""
        
# #         overall_decision = CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE]
# #         overall_decision_code = ModerationCategory.SAFE.value
# #         overall_confidence = 1.0
# #         flagged_content = []
        
# #         # Check audio
# #         if audio_result.category_code != ModerationCategory.SAFE.value:
# #             overall_decision = audio_result.category
# #             overall_decision_code = audio_result.category_code
# #             overall_confidence = audio_result.confidence
# #             flagged_content.append(f"🔊 Audio: {audio_result.category}")
        
# #         # Check frames
# #         flagged_categories = {}
# #         for frame in frame_results:
# #             if frame.category_code != ModerationCategory.SAFE.value:
# #                 if frame.category_code not in flagged_categories:
# #                     flagged_categories[frame.category_code] = []
# #                 flagged_categories[frame.category_code].append(frame.timestamp)
        
# #         # Aggregate flagged frames
# #         for cat_code, timestamps in flagged_categories.items():
# #             cat_display = CATEGORY_DISPLAY_NAMES[ModerationCategory(cat_code)]
# #             flagged_content.append(
# #                 f"🎞️  {cat_display}: {len(timestamps)} frames"
# #             )
            
# #             # Update overall decision if audio is safe
# #             if overall_decision_code == ModerationCategory.SAFE.value:
# #                 overall_decision = cat_display
# #                 overall_decision_code = cat_code
                
# #                 # Calculate average confidence of flagged frames
# #                 flagged_frames = [
# #                     f for f in frame_results
# #                     if f.category_code == cat_code
# #                 ]
# #                 avg_conf = sum(f.confidence for f in flagged_frames) / len(flagged_frames)
# #                 overall_confidence = round(avg_conf, 2)
        
# #         # Calculate summary
# #         total_frames = len(frame_results)
# #         flagged_frames_count = sum(
# #             1 for f in frame_results
# #             if f.category_code != ModerationCategory.SAFE.value
# #         )
        
# #         summary = VideoModerationSummary(
# #             total_frames=total_frames,
# #             flagged_frames=flagged_frames_count,
# #             flagged_percentage=round(
# #                 (flagged_frames_count / total_frames * 100) if total_frames > 0 else 0,
# #                 1
# #             ),
# #             audio_safe=(audio_result.category_code == ModerationCategory.SAFE.value)
# #         )
        
# #         return VideoModerationResponse(
# #             overall_decision=overall_decision,
# #             overall_decision_code=overall_decision_code,
# #             overall_confidence=overall_confidence,
# #             flagged_content=flagged_content,
# #             audio_moderation=audio_result,
# #             frame_moderation=frame_results,
# #             summary=summary
# #         )
    
# #     def _extract_audio(self, video_path: str) -> Optional[str]:
# #         """Extract audio track from video"""
# #         clip = None
# #         temp_audio_path = None
        
# #         try:
# #             clip = VideoFileClip(video_path)
            
# #             if clip.audio is None:
# #                 print("   ℹ️  No audio track found")
# #                 return None
            
# #             temp_audio_fd, temp_audio_path = tempfile.mkstemp(suffix='.wav', prefix='audio_')
# #             os.close(temp_audio_fd)
            
# #             clip.audio.write_audiofile(
# #                 temp_audio_path,
# #                 codec='pcm_s16le',
# #                 logger=None,
# #                 verbose=False,
# #                 fps=16000
# #             )
            
# #             print(f"   ✅ Audio extracted: {temp_audio_path}")
# #             return temp_audio_path
            
# #         except Exception as e:
# #             print(f"   Audio extraction error: {e}")
# #             if temp_audio_path and os.path.exists(temp_audio_path):
# #                 try:
# #                     os.remove(temp_audio_path)
# #                 except:
# #                     pass
# #             return None
# #         finally:
# #             if clip:
# #                 try:
# #                     clip.close()
# #                 except:
# #                     pass
    
# #     def _extract_frames(
# #         self,
# #         video_path: str,
# #         sampling_fps: float
# #     ) -> List[Dict]:
# #         """Extract frames from video at specified sampling rate"""
# #         cap = cv2.VideoCapture(video_path)
# #         if not cap.isOpened():
# #             print("   ❌ Failed to open video file")
# #             return []
        
# #         frames = []
# #         frame_count = 0
# #         video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
# #         interval = max(1, int(video_fps / sampling_fps))
        
# #         while True:
# #             ret, frame = cap.read()
# #             if not ret:
# #                 break
            
# #             if frame_count % interval == 0:
# #                 rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
# #                 pil_image = Image.fromarray(rgb_frame)
# #                 timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                
# #                 frames.append({
# #                     "timestamp_sec": timestamp,
# #                     "image": pil_image
# #                 })
            
# #             frame_count += 1
        
# #         cap.release()
# #         print(f"   ✅ Extracted {len(frames)} frames")
# #         return frames
    
# #     def _create_error_response(self, error_message: str) -> VideoModerationResponse:
# #         """Create error response"""
# #         return VideoModerationResponse(
# #             overall_decision="Error",
# #             overall_decision_code="error",
# #             overall_confidence=0.0,
# #             flagged_content=[error_message],
# #             audio_moderation=TextModerationResponse(
# #                 category="Error",
# #                 category_code="error",
# #                 confidence=0.0,
# #                 reasoning=error_message
# #             ),
# #             frame_moderation=[],
# #             summary=VideoModerationSummary(
# #                 total_frames=0,
# #                 flagged_frames=0,
# #                 flagged_percentage=0.0,
# #                 audio_safe=False
# #             )
# #         )



# # app/services/video_moderation.py (Updated with safe resource management and keyframe saving)
# """
# Video content moderation service with safe resource management.
# """
# import os
# import cv2
# import tempfile
# from pathlib import Path
# from PIL import Image
# from typing import List, Dict, Optional, Callable
# from moviepy.editor import VideoFileClip
# from datetime import datetime

# from src.schemas.models import (
#     ModerationCategory,
#     CATEGORY_DISPLAY_NAMES,
#     TextModerationResponse,
#     FrameModerationResult,
#     VideoModerationSummary,
#     VideoModerationResponse,
# )
# from src.services.text_moderation import TextModerationService
# from src.services.image_moderation import ImageModerationService
# from src.services.asr_service import ASRService
# from src.services.keyframe_detector import AdaptiveKeyframeDetector
# from src.utils.logging_utils import structured_logger
# from src.utils.file_utils import safe_remove_file
# from src.utils.config import get_settings


# class VideoModerationService:
#     """Service for moderating video content with safe resource management"""
    
#     def __init__(
#         self,
#         text_service: TextModerationService,
#         image_service: ImageModerationService,
#         asr_service: ASRService
#     ):
#         """
#         Initialize video moderation service.
        
#         Args:
#             text_service: Text moderation service instance
#             image_service: Image moderation service instance
#             asr_service: ASR service instance
#         """
#         self.text_service = text_service
#         self.image_service = image_service
#         self.asr_service = asr_service
#         self.keyframe_detector = AdaptiveKeyframeDetector(threshold=0.3)
#         self.settings = get_settings()
        
#         structured_logger.info("VideoModerationService initialized")
    
#     def moderate(
#         self,
#         video_path: str,
#         sampling_fps: float = 0.5,
#         progress_callback: Optional[Callable[[int, int], None]] = None,
#         use_keyframes: bool = False,
#         job_id: Optional[str] = None
#     ) -> VideoModerationResponse:
#         """
#         Moderate video content (audio + frames).
        
#         Args:
#             video_path: Path to video file
#             sampling_fps: Frame sampling rate (frames per second)
#             progress_callback: Optional callback for progress updates
#             use_keyframes: Use keyframe detection instead of uniform sampling
#             job_id: Job ID for logging
            
#         Returns:
#             VideoModerationResponse with comprehensive analysis
#         """
#         worker_name = f"VideoMod-{job_id[:8] if job_id else 'unknown'}"
        
#         structured_logger.info(
#             f"Starting video moderation: {Path(video_path).name}",
#             worker_name=worker_name
#         )
        
#         print(f"\n{'='*70}")
#         print(f"🎥 VIDEO MODERATION: {Path(video_path).name}")
#         print(f"   Job ID: {job_id}")
#         print(f"   Method: {'Keyframe Detection' if use_keyframes else f'Uniform Sampling @ {sampling_fps} fps'}")
#         print(f"{'='*70}")
        
#         if not video_path or not os.path.exists(video_path):
#             return self._create_error_response("Video file not found")
        
#         # Get video info
#         video_info = self._get_video_info(video_path)
#         print(f"   Duration: {video_info['duration']:.2f}s")
#         print(f"   FPS: {video_info['fps']:.2f}")
#         print(f"   Total Frames: {video_info['total_frames']}")
#         print(f"{'='*70}")
        
#         # Moderate audio
#         audio_result = self._moderate_audio(video_path, worker_name)
        
#         # Moderate frames
#         if use_keyframes:
#             frame_results = self._moderate_keyframes(
#                 video_path, 
#                 progress_callback, 
#                 worker_name,
#                 job_id
#             )
#         else:
#             frame_results = self._moderate_frames(
#                 video_path, 
#                 sampling_fps, 
#                 progress_callback, 
#                 worker_name,
#                 job_id
#             )
        
#         # Aggregate results
#         response = self._aggregate_results(audio_result, frame_results)
        
#         print(f"{'='*70}")
#         print(f"✅ RESULT: {response.overall_decision} ({response.overall_confidence:.0%})")
#         print(f"{'='*70}\n")
        
#         structured_logger.info(
#             f"Video moderation completed: {response.overall_decision}",
#             worker_name=worker_name
#         )
        
#         return response
    
#     def _get_video_info(self, video_path: str) -> dict:
#         """Get video information safely"""
#         cap = None
#         try:
#             cap = cv2.VideoCapture(video_path)
#             info = {
#                 'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
#                 'fps': cap.get(cv2.CAP_PROP_FPS) or 30,
#                 'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
#                 'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#             }
#             info['duration'] = info['total_frames'] / info['fps']
#             return info
#         finally:
#             if cap is not None:
#                 cap.release()
    
#     def _moderate_keyframes(
#         self,
#         video_path: str,
#         progress_callback: Optional[Callable],
#         worker_name: str,
#         job_id: Optional[str] = None
#     ) -> List[FrameModerationResult]:
#         """Moderate video using keyframe detection"""
#         print("🔑 Using keyframe detection...")
#         structured_logger.info("Starting keyframe detection", worker_name=worker_name)
        
#         try:
#             keyframes = self.keyframe_detector.detect(video_path)
            
#             if not keyframes:
#                 structured_logger.warning(
#                     "No keyframes detected, falling back to uniform sampling",
#                     worker_name=worker_name
#                 )
#                 return self._moderate_frames(video_path, 0.5, progress_callback, worker_name, job_id)
            
#             # Save keyframes if enabled
#             if self.settings.save_keyframes:
#                 self._save_keyframes(keyframes, job_id)
            
#             results = []
#             total_frames = len(keyframes)
            
#             print(f"📊 Processing {total_frames} keyframes...")
            
#             for i, keyframe_data in enumerate(keyframes):
#                 timestamp = keyframe_data["timestamp"]
#                 image = keyframe_data["image"]
#                 frame_idx = keyframe_data["frame_index"]
#                 importance = keyframe_data["importance_score"]
                
#                 # Log progress
#                 if i % self.settings.log_progress_interval == 0 or i == 0:
#                     structured_logger.info(
#                         f"Processing keyframe {i+1}/{total_frames} @ {timestamp:.1f}s (importance: {importance:.2f})",
#                         worker_name=worker_name
#                     )
                
#                 print(f"   Keyframe {i+1}/{total_frames} @ {timestamp:.1f}s (⭐{importance:.2f})", end=" ")
                
#                 moderation_result = self.image_service.moderate(image)
                
#                 frame_result = FrameModerationResult(
#                     timestamp=timestamp,
#                     frame_index=frame_idx,
#                     category=moderation_result.category,
#                     category_code=moderation_result.category_code,
#                     confidence=moderation_result.confidence,
#                     reasoning=moderation_result.reasoning,
#                     analysis=moderation_result.analysis
#                 )
                
#                 results.append(frame_result)
                
#                 status_icon = "✓" if moderation_result.category_code == "safe" else "⚠️ "
#                 print(f"{status_icon} {moderation_result.category}")
                
#                 # Progress callback
#                 if progress_callback:
#                     progress_callback(i + 1, total_frames)
            
#             structured_logger.info(
#                 f"Keyframe moderation completed: {len(results)} frames processed",
#                 worker_name=worker_name
#             )
            
#             return results
            
#         except Exception as e:
#             structured_logger.error(
#                 f"Keyframe detection failed: {e}",
#                 worker_name=worker_name
#             )
#             return self._moderate_frames(video_path, 0.5, progress_callback, worker_name, job_id)
    
#     def _save_keyframes(self, keyframes: List[Dict], job_id: Optional[str]):
#         """Save keyframes to disk for inspection"""
#         try:
#             output_dir = self.settings.ensure_keyframes_dir()
            
#             # Create subdirectory for this job
#             if job_id:
#                 job_dir = os.path.join(output_dir, job_id[:8])
#                 os.makedirs(job_dir, exist_ok=True)
#             else:
#                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 job_dir = os.path.join(output_dir, timestamp)
#                 os.makedirs(job_dir, exist_ok=True)
            
#             print(f"💾 Saving keyframes to: {job_dir}")
            
#             for i, keyframe_data in enumerate(keyframes):
#                 image = keyframe_data["image"]
#                 timestamp = keyframe_data["timestamp"]
#                 importance = keyframe_data["importance_score"]
                
#                 filename = f"keyframe_{i+1:03d}_t{timestamp:.2f}s_imp{importance:.2f}.jpg"
#                 filepath = os.path.join(job_dir, filename)
                
#                 image.save(filepath, quality=95)
            
#             print(f"   ✅ Saved {len(keyframes)} keyframes")
#             structured_logger.info(f"Saved {len(keyframes)} keyframes to {job_dir}")
            
#         except Exception as e:
#             print(f"   ⚠️  Failed to save keyframes: {e}")
#             structured_logger.warning(f"Failed to save keyframes: {e}")
    
#     def _moderate_audio(self, video_path: str, worker_name: str) -> TextModerationResponse:
#         """Extract and moderate audio from video"""
#         print("🔊 Processing audio...")
#         structured_logger.info("Starting audio extraction", worker_name=worker_name)
        
#         temp_audio_path = None
#         try:
#             temp_audio_path = self._extract_audio(video_path, worker_name)
            
#             if not temp_audio_path:
#                 return TextModerationResponse(
#                     category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
#                     category_code=ModerationCategory.SAFE.value,
#                     confidence=1.0,
#                     reasoning="No audio track"
#                 )
            
#             structured_logger.info("Starting speech transcription", worker_name=worker_name)
#             transcript = self.asr_service.transcribe(temp_audio_path)
            
#             if not transcript:
#                 return TextModerationResponse(
#                     category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
#                     category_code=ModerationCategory.SAFE.value,
#                     confidence=1.0,
#                     reasoning="No speech detected"
#                 )
            
#             structured_logger.info(
#                 f"Transcription completed: {len(transcript)} characters",
#                 worker_name=worker_name
#             )
            
#             result = self.text_service.moderate(transcript)
            
#             structured_logger.info(
#                 f"Audio moderation: {result.category} ({result.confidence:.2f})",
#                 worker_name=worker_name
#             )
            
#             return result
            
#         except Exception as e:
#             structured_logger.error(f"Audio moderation error: {e}", worker_name=worker_name)
#             return TextModerationResponse(
#                 category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
#                 category_code=ModerationCategory.SAFE.value,
#                 confidence=0.5,
#                 reasoning=f"Audio processing error: {str(e)[:50]}"
#             )
#         finally:
#             if temp_audio_path:
#                 safe_remove_file(temp_audio_path)
    
#     def _moderate_frames(
#         self,
#         video_path: str,
#         sampling_fps: float,
#         progress_callback: Optional[Callable],
#         worker_name: str,
#         job_id: Optional[str] = None
#     ) -> List[FrameModerationResult]:
#         """Extract and moderate video frames"""
#         print(f"🎞️  Processing frames (sampling @ {sampling_fps} fps)...")
#         structured_logger.info(
#             f"Starting frame extraction @ {sampling_fps} fps",
#             worker_name=worker_name
#         )
        
#         frames = self._extract_frames(video_path, sampling_fps, worker_name)
        
#         # Save frames if keyframe saving is enabled
#         if self.settings.save_keyframes:
#             self._save_extracted_frames(frames, job_id)
        
#         results = []
#         total_frames = len(frames)
        
#         for i, frame_data in enumerate(frames):
#             timestamp = frame_data["timestamp_sec"]
#             image = frame_data["image"]
            
#             # Log progress
#             if i % self.settings.log_progress_interval == 0 or i == 0:
#                 structured_logger.info(
#                     f"Processing frame {i+1}/{total_frames} @ {timestamp:.1f}s",
#                     worker_name=worker_name
#                 )
            
#             print(f"   Frame {i+1}/{total_frames} @ {timestamp:.1f}s", end=" ")
            
#             moderation_result = self.image_service.moderate(image)
            
#             frame_result = FrameModerationResult(
#                 timestamp=timestamp,
#                 frame_index=i,
#                 category=moderation_result.category,
#                 category_code=moderation_result.category_code,
#                 confidence=moderation_result.confidence,
#                 reasoning=moderation_result.reasoning,
#                 analysis=moderation_result.analysis
#             )
            
#             results.append(frame_result)
            
#             status_icon = "✓" if moderation_result.category_code == "safe" else "⚠️ "
#             print(f"{status_icon} {moderation_result.category}")
            
#             # Progress callback
#             if progress_callback:
#                 progress_callback(i + 1, total_frames)
        
#         structured_logger.info(
#             f"Frame moderation completed: {len(results)} frames processed",
#             worker_name=worker_name
#         )
        
#         return results
    
#     def _save_extracted_frames(self, frames: List[Dict], job_id: Optional[str]):
#         """Save extracted frames for inspection"""
#         try:
#             output_dir = self.settings.ensure_keyframes_dir()
            
#             if job_id:
#                 job_dir = os.path.join(output_dir, f"{job_id[:8]}_uniform")
#                 os.makedirs(job_dir, exist_ok=True)
#             else:
#                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 job_dir = os.path.join(output_dir, f"{timestamp}_uniform")
#                 os.makedirs(job_dir, exist_ok=True)
            
#             print(f"💾 Saving extracted frames to: {job_dir}")
            
#             for i, frame_data in enumerate(frames):
#                 image = frame_data["image"]
#                 timestamp = frame_data["timestamp_sec"]
                
#                 filename = f"frame_{i+1:03d}_t{timestamp:.2f}s.jpg"
#                 filepath = os.path.join(job_dir, filename)
                
#                 image.save(filepath, quality=95)
            
#             print(f"   ✅ Saved {len(frames)} frames")
            
#         except Exception as e:
#             print(f"   ⚠️  Failed to save frames: {e}")
    
#     def _aggregate_results(
#         self,
#         audio_result: TextModerationResponse,
#         frame_results: List[FrameModerationResult]
#     ) -> VideoModerationResponse:
#         """Aggregate audio and frame moderation results"""
        
#         overall_decision = CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE]
#         overall_decision_code = ModerationCategory.SAFE.value
#         overall_confidence = 1.0
#         flagged_content = []
        
#         # Check audio
#         if audio_result.category_code != ModerationCategory.SAFE.value:
#             overall_decision = audio_result.category
#             overall_decision_code = audio_result.category_code
#             overall_confidence = audio_result.confidence
#             flagged_content.append(f"🔊 Audio: {audio_result.category}")
        
#         # Check frames
#         flagged_categories = {}
#         for frame in frame_results:
#             if frame.category_code != ModerationCategory.SAFE.value:
#                 if frame.category_code not in flagged_categories:
#                     flagged_categories[frame.category_code] = []
#                 flagged_categories[frame.category_code].append(frame.timestamp)
        
#         # Aggregate flagged frames
#         for cat_code, timestamps in flagged_categories.items():
#             cat_display = CATEGORY_DISPLAY_NAMES[ModerationCategory(cat_code)]
#             flagged_content.append(
#                 f"🎞️  {cat_display}: {len(timestamps)} frames"
#             )
            
#             if overall_decision_code == ModerationCategory.SAFE.value:
#                 overall_decision = cat_display
#                 overall_decision_code = cat_code
                
#                 flagged_frames = [
#                     f for f in frame_results
#                     if f.category_code == cat_code
#                 ]
#                 avg_conf = sum(f.confidence for f in flagged_frames) / len(flagged_frames)
#                 overall_confidence = round(avg_conf, 2)
        
#         # Calculate summary
#         total_frames = len(frame_results)
#         flagged_frames_count = sum(
#             1 for f in frame_results
#             if f.category_code != ModerationCategory.SAFE.value
#         )
        
#         summary = VideoModerationSummary(
#             total_frames=total_frames,
#             flagged_frames=flagged_frames_count,
#             flagged_percentage=round(
#                 (flagged_frames_count / total_frames * 100) if total_frames > 0 else 0,
#                 1
#             ),
#             audio_safe=(audio_result.category_code == ModerationCategory.SAFE.value)
#         )
        
#         return VideoModerationResponse(
#             overall_decision=overall_decision,
#             overall_decision_code=overall_decision_code,
#             overall_confidence=overall_confidence,
#             flagged_content=flagged_content,
#             audio_moderation=audio_result,
#             frame_moderation=frame_results,
#             summary=summary
#         )
    
#     def _extract_audio(self, video_path: str, worker_name: str) -> Optional[str]:
#         """Extract audio track from video"""
#         clip = None
#         temp_audio_path = None
        
#         try:
#             clip = VideoFileClip(video_path)
            
#             if clip.audio is None:
#                 print("   ℹ️  No audio track found")
#                 return None
            
#             temp_audio_fd, temp_audio_path = tempfile.mkstemp(suffix='.wav', prefix='audio_')
#             os.close(temp_audio_fd)
            
#             clip.audio.write_audiofile(
#                 temp_audio_path,
#                 codec='pcm_s16le',
#                 logger=None,
#                 verbose=False,
#                 fps=16000
#             )
            
#             print(f"   ✅ Audio extracted: {temp_audio_path}")
#             return temp_audio_path
            
#         except Exception as e:
#             structured_logger.error(f"Audio extraction error: {e}", worker_name=worker_name)
#             if temp_audio_path:
#                 safe_remove_file(temp_audio_path)
#             return None
#         finally:
#             if clip:
#                 try:
#                     clip.close()
#                     del clip
#                 except:
#                     pass
    
#     def _extract_frames(
#         self,
#         video_path: str,
#         sampling_fps: float,
#         worker_name: str
#     ) -> List[Dict]:
#         """Extract frames from video at specified sampling rate with safe resource management"""
#         cap = None
#         try:
#             cap = cv2.VideoCapture(video_path)
            
#             if not cap.isOpened():
#                 structured_logger.error("Failed to open video file", worker_name=worker_name)
#                 return []
            
#             frames = []
#             frame_count = 0
#             video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
#             interval = max(1, int(video_fps / sampling_fps))
            
#             while True:
#                 ret, frame = cap.read()
#                 if not ret:
#                     break
                
#                 if frame_count % interval == 0:
#                     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                     pil_image = Image.fromarray(rgb_frame)
#                     timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                    
#                     frames.append({
#                         "timestamp_sec": timestamp,
#                         "image": pil_image
#                     })
                
#                 frame_count += 1
            
#             print(f"   ✅ Extracted {len(frames)} frames")
#             structured_logger.info(
#                 f"Extracted {len(frames)} frames from video",
#                 worker_name=worker_name
#             )
            
#             return frames
            
#         except Exception as e:
#             structured_logger.error(f"Frame extraction error: {e}", worker_name=worker_name)
#             return []
#         finally:
#             if cap is not None:
#                 try:
#                     cap.release()
#                     # Force garbage collection
#                     del cap
#                 except:
#                     pass
    
#     def _create_error_response(self, error_message: str) -> VideoModerationResponse:
#         """Create error response"""
#         return VideoModerationResponse(
#             overall_decision="Error",
#             overall_decision_code="error",
#             overall_confidence=0.0,
#             flagged_content=[error_message],
#             audio_moderation=TextModerationResponse(
#                 category="Error",
#                 category_code="error",
#                 confidence=0.0,
#                 reasoning=error_message
#             ),
#             frame_moderation=[],
#             summary=VideoModerationSummary(
#                 total_frames=0,
#                 flagged_frames=0,
#                 flagged_percentage=0.0,
#                 audio_safe=False
#             )
#         )


# app/services/video_moderation.py (Fixed keyframe logic + enhanced logging)
"""
Video content moderation service with intelligent keyframe detection.
"""
import os
import cv2
import tempfile
import time
from pathlib import Path
from PIL import Image
from typing import List, Dict, Optional, Callable
from moviepy.editor import VideoFileClip
from datetime import datetime

from src.schemas.models import (
    ModerationCategory,
    CATEGORY_DISPLAY_NAMES,
    TextModerationResponse,
    FrameModerationResult,
    VideoModerationSummary,
    VideoModerationResponse,
)
from src.services.text_moderation import TextModerationService
from src.services.image_moderation import ImageModerationService
from src.services.asr_service import ASRService
from src.services.keyframe_detector import AdaptiveKeyframeDetector
from src.utils.logging_utils import structured_logger
from src.utils.file_utils import safe_remove_file
from src.utils.config import get_settings


# class VideoModerationService:
#     """Service for moderating video content with intelligent frame selection"""
    
#     def __init__(
#         self,
#         text_service: TextModerationService,
#         image_service: ImageModerationService,
#         asr_service: ASRService
#     ):
#         """
#         Initialize video moderation service.
        
#         Args:
#             text_service: Text moderation service instance
#             image_service: Image moderation service instance
#             asr_service: ASR service instance
#         """
#         self.text_service = text_service
#         self.image_service = image_service
#         self.asr_service = asr_service
#         self.keyframe_detector = AdaptiveKeyframeDetector(threshold=0.3)
#         self.settings = get_settings()
        
#         structured_logger.info("VideoModerationService initialized")
    
#     def moderate(
#         self,
#         video_path: str,
#         sampling_fps: float = 0.5,
#         progress_callback: Optional[Callable[[int, int], None]] = None,
#         use_keyframes: bool = False,
#         job_id: Optional[str] = None
#     ) -> VideoModerationResponse:
#         """
#         Moderate video content with intelligent frame selection.
        
#         Args:
#             video_path: Path to video file
#             sampling_fps: Frame sampling rate (only used if use_keyframes=False)
#             progress_callback: Optional callback for progress updates
#             use_keyframes: Use keyframe detection for intelligent frame selection
#             job_id: Job ID for logging
            
#         Returns:
#             VideoModerationResponse with comprehensive analysis
#         """
#         worker_name = f"VideoMod-{job_id[:8] if job_id else 'unknown'}"
#         start_time = time.time()
        
#         structured_logger.info(
#             f"Starting video moderation: {Path(video_path).name}",
#             worker_name=worker_name
#         )
        
#         print(f"\n{'='*70}")
#         print(f"🎥 VIDEO MODERATION START")
#         print(f"{'='*70}")
#         print(f"   📁 File: {Path(video_path).name}")
#         print(f"   🆔 Job ID: {job_id}")
#         print(f"   🔧 Method: {'🔑 KEYFRAME DETECTION' if use_keyframes else f'⏱️  UNIFORM SAMPLING @ {sampling_fps} fps'}")
#         print(f"   👷 Worker: {worker_name}")
#         print(f"{'='*70}")
        
#         if not video_path or not os.path.exists(video_path):
#             return self._create_error_response("Video file not found")
        
#         # Get video info
#         video_info = self._get_video_info(video_path)
#         print(f"\n📊 VIDEO INFORMATION:")
#         print(f"   Duration: {video_info['duration']:.2f}s ({video_info['duration']/60:.1f} minutes)")
#         print(f"   FPS: {video_info['fps']:.2f}")
#         print(f"   Resolution: {video_info['width']}x{video_info['height']}")
#         print(f"   Total Frames: {video_info['total_frames']:,}")
        
#         # Calculate expected frames for comparison
#         if use_keyframes:
#             expected_frames = "TBD (adaptive)"
#         else:
#             expected_frames = int(video_info['duration'] * sampling_fps)
#         print(f"   Expected Frames to Process: {expected_frames}")
#         print(f"{'='*70}")
        
#         # Moderate audio
#         audio_start = time.time()
#         audio_result = self._moderate_audio(video_path, worker_name)
#         audio_time = time.time() - audio_start
#         print(f"\n⏱️  Audio processing time: {audio_time:.2f}s")
        
#         # Moderate frames - KEY LOGIC HERE
#         frame_start = time.time()
#         if use_keyframes:
#             print(f"\n{'='*70}")
#             print(f"🔑 KEYFRAME DETECTION MODE")
#             print(f"{'='*70}")
#             frame_results = self._moderate_keyframes(
#                 video_path, 
#                 progress_callback, 
#                 worker_name,
#                 job_id,
#                 video_info
#             )
#         else:
#             print(f"\n{'='*70}")
#             print(f"⏱️  UNIFORM SAMPLING MODE")
#             print(f"{'='*70}")
#             frame_results = self._moderate_frames(
#                 video_path, 
#                 sampling_fps, 
#                 progress_callback, 
#                 worker_name,
#                 job_id,
#                 video_info
#             )
        
#         frame_time = time.time() - frame_start
        
#         # Performance summary
#         print(f"\n{'='*70}")
#         print(f"⏱️  PERFORMANCE SUMMARY")
#         print(f"{'='*70}")
#         print(f"   Audio Processing: {audio_time:.2f}s")
#         print(f"   Frame Processing: {frame_time:.2f}s")
#         print(f"   Frames Processed: {len(frame_results)}")
#         print(f"   Avg Time/Frame: {frame_time/len(frame_results):.2f}s" if len(frame_results) > 0 else "   Avg Time/Frame: N/A")
        
#         if use_keyframes:
#             reduction = ((video_info['total_frames'] - len(frame_results)) / video_info['total_frames'] * 100)
#             print(f"   🎯 Frame Reduction: {reduction:.1f}% ({video_info['total_frames']:,} → {len(frame_results)})")
#             time_saved_estimate = (video_info['total_frames'] - len(frame_results)) * (frame_time/len(frame_results) if len(frame_results) > 0 else 0)
#             print(f"   💰 Estimated Time Saved: {time_saved_estimate:.1f}s")
        
#         # Aggregate results
#         response = self._aggregate_results(audio_result, frame_results)
        
#         total_time = time.time() - start_time
#         print(f"   🎯 Total Processing Time: {total_time:.2f}s")
#         print(f"{'='*70}")
        
#         print(f"\n{'='*70}")
#         print(f"✅ MODERATION RESULT: {response.overall_decision}")
#         print(f"{'='*70}")
#         print(f"   Confidence: {response.overall_confidence:.0%}")
#         print(f"   Flagged Content: {len(response.flagged_content)} issues")
#         if response.flagged_content:
#             for flag in response.flagged_content:
#                 print(f"      • {flag}")
#         print(f"{'='*70}\n")
        
#         structured_logger.info(
#             f"Video moderation completed: {response.overall_decision} "
#             f"(total: {total_time:.2f}s, frames: {len(frame_results)})",
#             worker_name=worker_name
#         )
        
#         return response
    
#     def _get_video_info(self, video_path: str) -> dict:
#         """Get video information safely"""
#         cap = None
#         try:
#             cap = cv2.VideoCapture(video_path)
#             info = {
#                 'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
#                 'fps': cap.get(cv2.CAP_PROP_FPS) or 30,
#                 'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
#                 'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#             }
#             info['duration'] = info['total_frames'] / info['fps']
#             return info
#         finally:
#             if cap is not None:
#                 cap.release()
    
#     def _moderate_keyframes(
#         self,
#         video_path: str,
#         progress_callback: Optional[Callable],
#         worker_name: str,
#         job_id: Optional[str],
#         video_info: dict
#     ) -> List[FrameModerationResult]:
#         """
#         Moderate video using intelligent keyframe detection.
#         This is the MAIN logic for reducing frame count while maintaining accuracy.
#         """
#         print(f"🔍 Starting keyframe detection analysis...")
#         structured_logger.info("Starting keyframe detection", worker_name=worker_name)
        
#         detection_start = time.time()
        
#         try:
#             # Detect keyframes
#             keyframes = self.keyframe_detector.detect(video_path)
            
#             detection_time = time.time() - detection_start
            
#             if not keyframes:
#                 print(f"⚠️  No keyframes detected!")
#                 structured_logger.warning(
#                     "No keyframes detected, falling back to uniform sampling",
#                     worker_name=worker_name
#                 )
#                 return self._moderate_frames(
#                     video_path, 0.5, progress_callback, worker_name, job_id, video_info
#                 )
            
#             # Display keyframe detection results
#             print(f"\n✅ Keyframe Detection Complete!")
#             print(f"   ⏱️  Detection Time: {detection_time:.2f}s")
#             print(f"   🎯 Keyframes Found: {len(keyframes)}")
#             print(f"   📊 Original Frames: {video_info['total_frames']:,}")
#             print(f"   📉 Reduction: {((video_info['total_frames'] - len(keyframes)) / video_info['total_frames'] * 100):.1f}%")
#             print(f"   📈 Coverage: {len(keyframes)/video_info['duration']*60:.1f} keyframes/minute")
#             print(f"\n🎬 KEYFRAME TIMESTAMPS:")
            
#             for i, kf in enumerate(keyframes):
#                 importance_bar = "█" * int(kf['importance_score'] * 10)
#                 print(f"   [{i+1:2d}] {kf['timestamp']:7.2f}s | "
#                       f"Frame {kf['frame_index']:6d} | "
#                       f"Importance: {importance_bar} {kf['importance_score']:.2f}")
            
#             print(f"\n{'='*70}")
            
#             # Save keyframes if enabled
#             if self.settings.save_keyframes:
#                 self._save_keyframes(keyframes, job_id, "keyframe")
            
#             # Moderate keyframes
#             results = []
#             total_frames = len(keyframes)
            
#             print(f"\n🔬 MODERATING {total_frames} KEYFRAMES:")
#             print(f"{'='*70}")
            
#             moderation_start = time.time()
            
#             for i, keyframe_data in enumerate(keyframes):
#                 frame_start_time = time.time()
                
#                 timestamp = keyframe_data["timestamp"]
#                 image = keyframe_data["image"]
#                 frame_idx = keyframe_data["frame_index"]
#                 importance = keyframe_data["importance_score"]
                
#                 # Log progress at intervals
#                 if i % self.settings.log_progress_interval == 0 or i == 0:
#                     elapsed = time.time() - moderation_start
#                     if i > 0:
#                         avg_time = elapsed / i
#                         remaining = avg_time * (total_frames - i)
#                         print(f"\n📊 Progress: {i}/{total_frames} ({i/total_frames*100:.1f}%) | "
#                               f"Elapsed: {elapsed:.1f}s | ETA: {remaining:.1f}s")
                    
#                     structured_logger.info(
#                         f"Processing keyframe {i+1}/{total_frames} @ {timestamp:.1f}s "
#                         f"(importance: {importance:.2f})",
#                         worker_name=worker_name
#                     )
                
#                 print(f"   [KF {i+1:2d}/{total_frames}] ", end="")
#                 print(f"t={timestamp:6.2f}s | f={frame_idx:6d} | ⭐{importance:.2f} | ", end="")
                
#                 # Moderate this keyframe
#                 moderation_result = self.image_service.moderate(image)
                
#                 frame_result = FrameModerationResult(
#                     timestamp=timestamp,
#                     frame_index=frame_idx,
#                     category=moderation_result.category,
#                     category_code=moderation_result.category_code,
#                     confidence=moderation_result.confidence,
#                     reasoning=moderation_result.reasoning,
#                     analysis=moderation_result.analysis
#                 )
                
#                 results.append(frame_result)
                
#                 # Status with color coding
#                 if moderation_result.category_code == "safe":
#                     status = f"✅ Safe"
#                 else:
#                     status = f"⚠️  {moderation_result.category} ({moderation_result.confidence:.0%})"
                
#                 frame_time = time.time() - frame_start_time
#                 print(f"{status} | ⏱️ {frame_time:.2f}s")
                
#                 # Progress callback
#                 if progress_callback:
#                     progress_callback(i + 1, total_frames)
            
#             total_moderation_time = time.time() - moderation_start
            
#             print(f"\n{'='*70}")
#             print(f"✅ KEYFRAME MODERATION COMPLETE")
#             print(f"{'='*70}")
#             print(f"   Total Keyframes: {len(results)}")
#             print(f"   Moderation Time: {total_moderation_time:.2f}s")
#             print(f"   Avg Time/Keyframe: {total_moderation_time/len(results):.2f}s")
#             print(f"{'='*70}")
            
#             structured_logger.info(
#                 f"Keyframe moderation completed: {len(results)} frames processed "
#                 f"in {total_moderation_time:.2f}s",
#                 worker_name=worker_name
#             )
            
#             return results
            
#         except Exception as e:
#             structured_logger.error(
#                 f"Keyframe detection failed: {e}",
#                 worker_name=worker_name
#             )
#             print(f"\n❌ Keyframe detection failed: {e}")
#             print(f"   Falling back to uniform sampling...")
#             return self._moderate_frames(
#                 video_path, 0.5, progress_callback, worker_name, job_id, video_info
#             )
    
#     def _save_keyframes(self, keyframes: List[Dict], job_id: Optional[str], mode: str = "keyframe"):
#         """Save keyframes to disk for inspection"""
#         try:
#             output_dir = self.settings.ensure_keyframes_dir()
            
#             # Create subdirectory for this job
#             if job_id:
#                 job_dir = os.path.join(output_dir, f"{job_id[:8]}_{mode}")
#             else:
#                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 job_dir = os.path.join(output_dir, f"{timestamp}_{mode}")
            
#             os.makedirs(job_dir, exist_ok=True)
            
#             print(f"\n💾 Saving {len(keyframes)} {mode}s to: {job_dir}")
            
#             for i, keyframe_data in enumerate(keyframes):
#                 image = keyframe_data["image"]
#                 timestamp = keyframe_data["timestamp"]
#                 importance = keyframe_data.get("importance_score", 0.5)
#                 frame_idx = keyframe_data.get("frame_index", i)
                
#                 filename = f"{mode}_{i+1:03d}_f{frame_idx:06d}_t{timestamp:.2f}s_imp{importance:.2f}.jpg"
#                 filepath = os.path.join(job_dir, filename)
                
#                 image.save(filepath, quality=95)
            
#             print(f"   ✅ Saved {len(keyframes)} {mode}s successfully")
#             structured_logger.info(f"Saved {len(keyframes)} {mode}s to {job_dir}")
            
#         except Exception as e:
#             print(f"   ⚠️  Failed to save {mode}s: {e}")
#             structured_logger.warning(f"Failed to save {mode}s: {e}")

from src.schemas.models import (
    ModerationCategory,
    CATEGORY_DISPLAY_NAMES,
    KeyframeMethod,
    TextModerationResponse,
    FrameModerationResult,
    VideoModerationSummary,
    VideoModerationResponse,
)
from src.services.keyframe_detectors import create_keyframe_detector
from src.utils.logging_utils import structured_logger
from src.utils.file_utils import safe_remove_file
from src.utils.keyframe_storage import KeyframeStorage


class VideoModerationService:
    """Service for moderating video content with multiple keyframe strategies"""
    
    def __init__(
        self,
        text_service: TextModerationService,
        image_service: ImageModerationService,
        asr_service: ASRService
    ):
        """Initialize video moderation service"""
        self.text_service = text_service
        self.image_service = image_service
        self.asr_service = asr_service
        self.settings = get_settings()
        # self.keyframe_storage = KeyframeStorage(self.settings.keyframes_output_dir)
        self.keyframe_storage = KeyframeStorage(
            base_dir=self.settings.keyframes_output_dir,
            organize_by_category=self.settings.keyframes_organize_by_category,
            include_safe=self.settings.keyframes_include_safe
        )
        
        structured_logger.info("VideoModerationService initialized")
    
    def moderate(
        self,
        video_path: str,
        sampling_fps: float = 0.5,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        keyframe_method: KeyframeMethod = KeyframeMethod.UNIFORM,
        job_id: Optional[str] = None,
        # Scene detection parameters
        scene_detector_type: str = "content",
        scene_threshold: float = 15.0,
        min_scene_length: float = 1.0
    ) -> VideoModerationResponse:
        """
        Moderate video content with intelligent frame selection.
        
        Args:
            video_path: Path to video file
            sampling_fps: Frame sampling rate (for UNIFORM method)
            progress_callback: Progress callback
            keyframe_method: Frame selection method
            job_id: Job ID for logging
            scene_detector_type: PySceneDetect detector type
            scene_threshold: Scene detection threshold
            min_scene_length: Minimum scene length
            
        Returns:
            VideoModerationResponse
        """
        worker_name = f"VideoMod-{job_id[:8] if job_id else 'unknown'}"
        start_time = time.time()
        
        structured_logger.info(
            f"Starting video moderation: {Path(video_path).name}",
            worker_name=worker_name
        )
        
        # Display header
        method_display = {
            KeyframeMethod.UNIFORM: f"⏱️  UNIFORM SAMPLING @ {sampling_fps} fps",
            KeyframeMethod.DIFFERENCE: "🔍 FRAME DIFFERENCE ANALYSIS",
            KeyframeMethod.SCENE: f"🎬 SCENE DETECTION ({scene_detector_type})"
        }
        
        print(f"\n{'='*70}")
        print(f"🎥 VIDEO MODERATION START")
        print(f"{'='*70}")
        print(f"   📁 File: {Path(video_path).name}")
        print(f"   🆔 Job ID: {job_id}")
        print(f"   🔧 Method: {method_display[keyframe_method]}")
        print(f"   👷 Worker: {worker_name}")
        print(f"{'='*70}")
        
        if not video_path or not os.path.exists(video_path):
            return self._create_error_response("Video file not found")
        
        # Get video info
        video_info = self._get_video_info(video_path)
        self._print_video_info(video_info, keyframe_method, sampling_fps)
        
        # Moderate audio
        audio_start = time.time()
        audio_result = self._moderate_audio(video_path, worker_name)
        audio_time = time.time() - audio_start
        print(f"\n⏱️  Audio processing time: {audio_time:.2f}s")
        
        # Moderate frames
        frame_start = time.time()
        frame_results, keyframes = self._moderate_frames_with_method(
            video_path=video_path,
            keyframe_method=keyframe_method,
            sampling_fps=sampling_fps,
            progress_callback=progress_callback,
            worker_name=worker_name,
            job_id=job_id,
            video_info=video_info,
            scene_detector_type=scene_detector_type,
            scene_threshold=scene_threshold,
            min_scene_length=min_scene_length
        )
        frame_time = time.time() - frame_start
        
        # Save keyframes if enabled
        # if self.settings.save_keyframes and keyframes:
        #     self._save_keyframes_to_storage(
        #         keyframes=keyframes,
        #         job_id=job_id,
        #         video_name=Path(video_path).stem,
        #         method=keyframe_method.value
        #     )
        if self.settings.save_keyframes and keyframes:
            self._save_keyframes_with_results(
                keyframes=keyframes,
                frame_results=frame_results,
                job_id=job_id,
                video_name=Path(video_path).stem,
                method=keyframe_method.value
            )
        
        # Performance summary
        self._print_performance_summary(
            audio_time=audio_time,
            frame_time=frame_time,
            frame_count=len(frame_results),
            video_info=video_info,
            keyframe_method=keyframe_method
        )
        
        # Aggregate results
        response = self._aggregate_results(audio_result, frame_results)
        
        total_time = time.time() - start_time
        print(f"   🎯 Total Processing Time: {total_time:.2f}s")
        print(f"{'='*70}")
        
        self._print_final_result(response)
        
        structured_logger.info(
            f"Video moderation completed: {response.overall_decision} "
            f"(total: {total_time:.2f}s, frames: {len(frame_results)})",
            worker_name=worker_name
        )
        
        return response
    
    def _save_keyframes_with_results(
        self,
        keyframes: List[Dict],
        frame_results: List[FrameModerationResult],
        job_id: Optional[str],
        video_name: str,
        method: str
    ):
        """Save keyframes with moderation results organized by category"""
        try:
            run_folder = self.keyframe_storage.create_run_folder(
                job_id=job_id,
                method=method,
                video_name=video_name
            )
            
            # Convert frame results to dict format
            moderation_results = [
                {
                    "category": result.category,
                    "category_code": result.category_code,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning
                }
                for result in frame_results
            ]
            
            # Save with results
            self.keyframe_storage.save_keyframes_with_results(
                keyframes=keyframes,
                moderation_results=moderation_results,
                run_folder=run_folder,
                video_name=video_name
            )
            
        except Exception as e:
            print(f"⚠️  Failed to save keyframes: {e}")
            structured_logger.warning(f"Failed to save keyframes: {e}")
    
    def _moderate_frames_with_method(
        self,
        video_path: str,
        keyframe_method: KeyframeMethod,
        sampling_fps: float,
        progress_callback: Optional[Callable],
        worker_name: str,
        job_id: Optional[str],
        video_info: dict,
        scene_detector_type: str,
        scene_threshold: float,
        min_scene_length: float
    ) -> tuple:
        """
        Moderate frames using specified method.
        
        Returns:
            Tuple of (frame_results, keyframes_list)
        """
        print(f"\n{'='*70}")
        
        if keyframe_method == KeyframeMethod.UNIFORM:
            print(f"⏱️  UNIFORM SAMPLING MODE")
            print(f"{'='*70}")
            frames = self._extract_frames(video_path, sampling_fps, worker_name)
            keyframes = self._frames_to_keyframes(frames)
            
        elif keyframe_method == KeyframeMethod.DIFFERENCE:
            print(f"🔍 FRAME DIFFERENCE MODE")
            print(f"{'='*70}")
            detector = create_keyframe_detector("difference")
            keyframes = detector.detect(video_path)
            
        elif keyframe_method == KeyframeMethod.SCENE:
            print(f"🎬 SCENE DETECTION MODE")
            print(f"{'='*70}")
            detector = create_keyframe_detector(
                "scene",
                detector_type=scene_detector_type,
                threshold=scene_threshold,
                min_scene_length=min_scene_length
            )
            keyframes = detector.detect(video_path)
            
        else:
            raise ValueError(f"Unknown keyframe method: {keyframe_method}")
        
        # Moderate keyframes
        results = self._moderate_keyframes(
            keyframes=keyframes,
            progress_callback=progress_callback,
            worker_name=worker_name,
            method_name=keyframe_method.value
        )
        
        return results, keyframes
    
    def _moderate_keyframes(
        self,
        keyframes: List[Dict],
        progress_callback: Optional[Callable],
        worker_name: str,
        method_name: str
    ) -> List[FrameModerationResult]:
        """Moderate extracted keyframes"""
        results = []
        total_frames = len(keyframes)
        
        print(f"\n🔬 MODERATING {total_frames} KEYFRAMES:")
        print(f"{'='*70}")
        
        moderation_start = time.time()
        
        for i, keyframe_data in enumerate(keyframes):
            frame_start_time = time.time()
            
            timestamp = keyframe_data["timestamp"]
            image = keyframe_data["image"]
            frame_idx = keyframe_data["frame_index"]
            importance = keyframe_data["importance_score"]
            metadata = keyframe_data.get("metadata", {})
            
            # Log progress
            if i % self.settings.log_progress_interval == 0 or i == 0:
                elapsed = time.time() - moderation_start
                if i > 0:
                    avg_time = elapsed / i
                    remaining = avg_time * (total_frames - i)
                    print(f"\n📊 Progress: {i}/{total_frames} ({i/total_frames*100:.1f}%) | "
                          f"Elapsed: {elapsed:.1f}s | ETA: {remaining:.1f}s")
                
                structured_logger.info(
                    f"Processing keyframe {i+1}/{total_frames} @ {timestamp:.1f}s "
                    f"(importance: {importance:.2f})",
                    worker_name=worker_name
                )
            
            print(f"   [KF {i+1:2d}/{total_frames}] ", end="")
            print(f"t={timestamp:6.2f}s | f={frame_idx:6d} | ⭐{importance:.2f} | ", end="")
            
            # Moderate
            moderation_result = self.image_service.moderate(image)
            
            frame_result = FrameModerationResult(
                timestamp=timestamp,
                frame_index=frame_idx,
                category=moderation_result.category,
                category_code=moderation_result.category_code,
                confidence=moderation_result.confidence,
                reasoning=moderation_result.reasoning,
                analysis=moderation_result.analysis
            )
            
            results.append(frame_result)
            
            # Status
            if moderation_result.category_code == "safe":
                status = f"✅ Safe"
            else:
                status = f"⚠️  {moderation_result.category} ({moderation_result.confidence:.0%})"
            
            frame_time = time.time() - frame_start_time
            print(f"{status} | ⏱️ {frame_time:.2f}s")
            
            if progress_callback:
                progress_callback(i + 1, total_frames)
        
        total_moderation_time = time.time() - moderation_start
        
        print(f"\n{'='*70}")
        print(f"✅ KEYFRAME MODERATION COMPLETE")
        print(f"{'='*70}")
        print(f"   Total Keyframes: {len(results)}")
        print(f"   Moderation Time: {total_moderation_time:.2f}s")
        print(f"   Avg Time/Keyframe: {total_moderation_time/len(results):.2f}s")
        print(f"{'='*70}")
        
        return results
    
    def _save_keyframes_to_storage(
        self,
        keyframes: List[Dict],
        job_id: Optional[str],
        video_name: str,
        method: str
    ):
        """Save keyframes using KeyframeStorage"""
        try:
            run_folder = self.keyframe_storage.create_run_folder(
                job_id=job_id,
                method=method,
                video_name=video_name
            )
            
            self.keyframe_storage.save_keyframes(
                keyframes=keyframes,
                run_folder=run_folder,
                video_name=video_name
            )
            
        except Exception as e:
            print(f"⚠️  Failed to save keyframes: {e}")
            structured_logger.warning(f"Failed to save keyframes: {e}")
    
    def _frames_to_keyframes(self, frames: List[Dict]) -> List[Dict]:
        """Convert uniform frames to keyframe format"""
        return [
            {
                "frame_index": i,
                "timestamp": f["timestamp_sec"],
                "image": f["image"],
                "importance_score": 0.5,
                "metadata": {"method": "uniform"}
            }
            for i, f in enumerate(frames)
        ]
    
    def _get_video_info(self, video_path: str) -> dict:
        """Get video information"""
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            info = {
                'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'fps': cap.get(cv2.CAP_PROP_FPS) or 30,
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            }
            info['duration'] = info['total_frames'] / info['fps']
            return info
        finally:
            if cap is not None:
                cap.release()
    
    def _print_video_info(self, video_info: dict, method: KeyframeMethod, sampling_fps: float):
        """Print video information"""
        print(f"\n📊 VIDEO INFORMATION:")
        print(f"   Duration: {video_info['duration']:.2f}s ({video_info['duration']/60:.1f} minutes)")
        print(f"   FPS: {video_info['fps']:.2f}")
        print(f"   Resolution: {video_info['width']}x{video_info['height']}")
        print(f"   Total Frames: {video_info['total_frames']:,}")
        
        if method == KeyframeMethod.UNIFORM:
            expected = int(video_info['duration'] * sampling_fps)
            print(f"   Expected Frames to Process: {expected}")
        else:
            print(f"   Expected Frames to Process: TBD (adaptive)")
        
        print(f"{'='*70}")
    
    def _print_performance_summary(
        self,
        audio_time: float,
        frame_time: float,
        frame_count: int,
        video_info: dict,
        keyframe_method: KeyframeMethod
    ):
        """Print performance summary"""
        print(f"\n{'='*70}")
        print(f"⏱️  PERFORMANCE SUMMARY")
        print(f"{'='*70}")
        print(f"   Audio Processing: {audio_time:.2f}s")
        print(f"   Frame Processing: {frame_time:.2f}s")
        print(f"   Frames Processed: {frame_count}")
        
        if frame_count > 0:
            print(f"   Avg Time/Frame: {frame_time/frame_count:.2f}s")
        
        if keyframe_method != KeyframeMethod.UNIFORM:
            reduction = ((video_info['total_frames'] - frame_count) / video_info['total_frames'] * 100)
            print(f"   🎯 Frame Reduction: {reduction:.1f}% ({video_info['total_frames']:,} → {frame_count})")
            
            if frame_count > 0:
                time_saved_estimate = (video_info['total_frames'] - frame_count) * (frame_time/frame_count)
                print(f"   💰 Estimated Time Saved: {time_saved_estimate:.1f}s ({time_saved_estimate/60:.1f} min)")
    
    def _print_final_result(self, response: VideoModerationResponse):
        """Print final moderation result"""
        print(f"\n{'='*70}")
        print(f"✅ MODERATION RESULT: {response.overall_decision}")
        print(f"{'='*70}")
        print(f"   Confidence: {response.overall_confidence:.0%}")
        print(f"   Flagged Content: {len(response.flagged_content)} issues")
        if response.flagged_content:
            for flag in response.flagged_content:
                print(f"      • {flag}")
        print(f"{'='*70}\n")
    
    
    def _moderate_audio(self, video_path: str, worker_name: str) -> TextModerationResponse:
        """Extract and moderate audio from video"""
        print(f"\n{'='*70}")
        print(f"🔊 AUDIO PROCESSING")
        print(f"{'='*70}")
        
        structured_logger.info("Starting audio extraction", worker_name=worker_name)
        
        temp_audio_path = None
        try:
            extraction_start = time.time()
            temp_audio_path = self._extract_audio(video_path, worker_name)
            extraction_time = time.time() - extraction_start
            
            if not temp_audio_path:
                print(f"   ℹ️  No audio track found")
                return TextModerationResponse(
                    category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
                    category_code=ModerationCategory.SAFE.value,
                    confidence=1.0,
                    reasoning="No audio track"
                )
            
            print(f"   ⏱️  Extraction time: {extraction_time:.2f}s")
            
            structured_logger.info("Starting speech transcription", worker_name=worker_name)
            
            transcription_start = time.time()
            transcript = self.asr_service.transcribe(temp_audio_path)
            transcription_time = time.time() - transcription_start
            
            if not transcript:
                print(f"   ℹ️  No speech detected")
                return TextModerationResponse(
                    category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
                    category_code=ModerationCategory.SAFE.value,
                    confidence=1.0,
                    reasoning="No speech detected"
                )
            
            print(f"   ⏱️  Transcription time: {transcription_time:.2f}s")
            print(f"   📝 Transcript length: {len(transcript)} characters")
            print(f"   📄 Preview: {transcript[:500]}..." if len(transcript) > 100 else f"   📄 Text: {transcript}")
            
            structured_logger.info(
                f"Transcription completed: {len(transcript)} characters in {transcription_time:.2f}s",
                worker_name=worker_name
            )
            
            moderation_start = time.time()
            result = self.text_service.moderate(transcript)
            moderation_time = time.time() - moderation_start
            
            print(f"   ⏱️  Moderation time: {moderation_time:.2f}s")
            print(f"   🎯 Result: {result.category} (confidence: {result.confidence:.0%})")
            print(f"   💭 Reasoning: {result.reasoning}")
            print(f"{'='*70}")
            
            structured_logger.info(
                f"Audio moderation: {result.category} ({result.confidence:.2f})",
                worker_name=worker_name
            )
            
            return result
            
        except Exception as e:
            structured_logger.error(f"Audio moderation error: {e}", worker_name=worker_name)
            print(f"   ❌ Error: {e}")
            print(f"{'='*70}")
            return TextModerationResponse(
                category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
                category_code=ModerationCategory.SAFE.value,
                confidence=0.5,
                reasoning=f"Audio processing error: {str(e)[:50]}"
            )
        finally:
            if temp_audio_path:
                safe_remove_file(temp_audio_path)
    
    def _moderate_frames(
        self,
        video_path: str,
        sampling_fps: float,
        progress_callback: Optional[Callable],
        worker_name: str,
        job_id: Optional[str],
        video_info: dict
    ) -> List[FrameModerationResult]:
        """Extract and moderate video frames using uniform sampling"""
        print(f"⏱️  Using uniform sampling at {sampling_fps} fps")
        print(f"   Expected frames: ~{int(video_info['duration'] * sampling_fps)}")
        
        structured_logger.info(
            f"Starting frame extraction @ {sampling_fps} fps",
            worker_name=worker_name
        )
        
        extraction_start = time.time()
        frames = self._extract_frames(video_path, sampling_fps, worker_name)
        extraction_time = time.time() - extraction_start
        
        print(f"   ⏱️  Extraction time: {extraction_time:.2f}s")
        print(f"   📊 Extracted: {len(frames)} frames")
        
        # Save frames if enabled
        if self.settings.save_keyframes:
            self._save_extracted_frames(frames, job_id)
        
        results = []
        total_frames = len(frames)
        
        print(f"\n🔬 MODERATING {total_frames} FRAMES:")
        print(f"{'='*70}")
        
        moderation_start = time.time()
        
        for i, frame_data in enumerate(frames):
            frame_start_time = time.time()
            
            timestamp = frame_data["timestamp_sec"]
            image = frame_data["image"]
            
            # Log progress
            if i % self.settings.log_progress_interval == 0 or i == 0:
                elapsed = time.time() - moderation_start
                if i > 0:
                    avg_time = elapsed / i
                    remaining = avg_time * (total_frames - i)
                    print(f"\n📊 Progress: {i}/{total_frames} ({i/total_frames*100:.1f}%) | "
                          f"Elapsed: {elapsed:.1f}s | ETA: {remaining:.1f}s")
                
                structured_logger.info(
                    f"Processing frame {i+1}/{total_frames} @ {timestamp:.1f}s",
                    worker_name=worker_name
                )
            
            print(f"   [Frame {i+1:3d}/{total_frames}] t={timestamp:6.2f}s | ", end="")
            
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
            
            # Status
            if moderation_result.category_code == "safe":
                status = f"✅ Safe"
            else:
                status = f"⚠️  {moderation_result.category} ({moderation_result.confidence:.0%})"
            
            frame_time = time.time() - frame_start_time
            print(f"{status} | ⏱️ {frame_time:.2f}s")
            
            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total_frames)
        
        total_moderation_time = time.time() - moderation_start
        
        print(f"\n{'='*70}")
        print(f"✅ FRAME MODERATION COMPLETE")
        print(f"{'='*70}")
        print(f"   Total Frames: {len(results)}")
        print(f"   Moderation Time: {total_moderation_time:.2f}s")
        print(f"   Avg Time/Frame: {total_moderation_time/len(results):.2f}s")
        print(f"{'='*70}")
        
        structured_logger.info(
            f"Frame moderation completed: {len(results)} frames processed in {total_moderation_time:.2f}s",
            worker_name=worker_name
        )
        
        return results
    
    def _save_extracted_frames(self, frames: List[Dict], job_id: Optional[str]):
        """Save extracted frames for inspection"""
        frame_data = [
            {
                "image": f["image"],
                "timestamp": f["timestamp_sec"],
                "frame_index": i,
                "importance_score": 0.5
            }
            for i, f in enumerate(frames)
        ]
        self._save_keyframes(frame_data, job_id, "uniform")
    
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
            flagged_content.append(f"🔊 Audio: {audio_result.category} ({audio_result.confidence:.0%})")
        
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
                f"🎞️  {cat_display}: {len(timestamps)} frames @ "
                f"{', '.join(f'{t:.1f}s' for t in timestamps[:3])}"
                f"{'...' if len(timestamps) > 3 else ''}"
            )
            
            if overall_decision_code == ModerationCategory.SAFE.value:
                overall_decision = cat_display
                overall_decision_code = cat_code
                
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
    
    def _extract_audio(self, video_path: str, worker_name: str) -> Optional[str]:
        """Extract audio track from video"""
        clip = None
        temp_audio_path = None
        
        try:
            clip = VideoFileClip(video_path)
            
            if clip.audio is None:
                return None
            
            temp_audio_fd, temp_audio_path = tempfile.mkstemp(suffix='.wav', prefix='audio_')
            os.close(temp_audio_fd)
            
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
            structured_logger.error(f"Audio extraction error: {e}", worker_name=worker_name)
            if temp_audio_path:
                safe_remove_file(temp_audio_path)
            return None
        finally:
            if clip:
                try:
                    clip.close()
                    del clip
                except:
                    pass
    
    def _extract_frames(
        self,
        video_path: str,
        sampling_fps: float,
        worker_name: str
    ) -> List[Dict]:
        """Extract frames from video at specified sampling rate"""
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                structured_logger.error("Failed to open video file", worker_name=worker_name)
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
            
            return frames
            
        except Exception as e:
            structured_logger.error(f"Frame extraction error: {e}", worker_name=worker_name)
            return []
        finally:
            if cap is not None:
                try:
                    cap.release()
                    del cap
                except:
                    pass
    
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