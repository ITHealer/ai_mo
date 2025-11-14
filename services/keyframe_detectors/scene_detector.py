# app/services/keyframe_detectors/scene_detector.py
"""
Scene-based keyframe detection using PySceneDetect.
"""
import cv2
from typing import List, Dict
from PIL import Image
from pathlib import Path

try:
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector, AdaptiveDetector
    PYSCENEDETECT_AVAILABLE = True
except ImportError:
    PYSCENEDETECT_AVAILABLE = False
    print("⚠️  PySceneDetect not available. Install with: pip install scenedetect[opencv]")

from .base import BaseKeyframeDetector


class SceneKeyframeDetector(BaseKeyframeDetector):
    """
    Keyframe detection using scene change detection (PySceneDetect).
    Detects scene boundaries and selects one keyframe per scene.
    """
    
    def __init__(
        self,
        detector_type: str = "content",
        threshold: float = 27.0,
        min_scene_length: float = 1.0
    ):
        """
        Initialize scene-based detector.
        
        Args:
            detector_type: "content" or "adaptive"
            threshold: Scene detection sensitivity
                - ContentDetector: typical range 15-35 (lower = more sensitive)
                - AdaptiveDetector: typical range 2-5
            min_scene_length: Minimum scene length in seconds
        """
        if not PYSCENEDETECT_AVAILABLE:
            raise ImportError(
                "PySceneDetect is required for scene detection. "
                "Install with: pip install scenedetect[opencv]"
            )
        
        super().__init__(
            detector_type=detector_type,
            threshold=threshold,
            min_scene_length=min_scene_length
        )
        self.detector_type = detector_type
        self.threshold = threshold
        self.min_scene_length = min_scene_length
    
    def get_method_name(self) -> str:
        return f"Scene Detection ({self.detector_type.capitalize()})"
    
    def detect(self, video_path: str) -> List[Dict]:
        """
        Detect keyframes using scene detection.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of keyframe info dictionaries
        """
        print(f"\n🎬 SCENE-BASED KEYFRAME DETECTION")
        print(f"{'='*70}")
        
        # Get video info
        video_info = self._get_video_info(video_path)
        fps = video_info['fps']
        duration = video_info['duration']
        
        print(f"   Video: {duration:.1f}s ({video_info['total_frames']} frames @ {fps:.1f} fps)")
        print(f"   Detector: {self.detector_type}")
        print(f"   Threshold: {self.threshold}")
        print(f"   Min Scene Length: {self.min_scene_length}s")
        print(f"{'='*70}")
        
        # Detect scenes
        print(f"\n🔍 Detecting scene changes...")
        scenes = self._detect_scenes(video_path, fps)
        
        if not scenes:
            print(f"⚠️  No scenes detected, using single keyframe")
            return self._single_keyframe_fallback(video_path)
        
        print(f"\n✅ Scene Detection Complete:")
        print(f"   Scenes Found: {len(scenes)}")
        print(f"   Avg Scene Length: {duration/len(scenes):.2f}s")
        print(f"   Keyframes to Extract: {len(scenes)}")
        
        # Extract keyframes (middle frame of each scene)
        keyframes = self._extract_keyframes_from_scenes(video_path, scenes, fps)
        
        print(f"\n📊 Scene Summary:")
        for i, kf in enumerate(keyframes):
            scene_start = kf['metadata']['scene_start']
            scene_end = kf['metadata']['scene_end']
            scene_duration = scene_end - scene_start
            print(f"   Scene {i+1:2d}: {scene_start:6.2f}s - {scene_end:6.2f}s "
                  f"(duration: {scene_duration:.2f}s) → "
                  f"Keyframe @ {kf['timestamp']:.2f}s (frame {kf['frame_index']})")
        
        print(f"{'='*70}\n")
        
        return keyframes
    
    def _detect_scenes(self, video_path: str, fps: float) -> List:
        """Detect scenes using PySceneDetect"""
        min_scene_len_frames = max(1, int(fps * self.min_scene_length))
        
        video_manager = VideoManager([video_path])
        scene_manager = SceneManager()
        
        # Choose detector
        if self.detector_type == "adaptive":
            detector = AdaptiveDetector(
                adaptive_threshold=self.threshold,
                min_scene_len=min_scene_len_frames,
            )
        else:
            detector = ContentDetector(
                threshold=self.threshold,
                min_scene_len=min_scene_len_frames,
            )
        
        scene_manager.add_detector(detector)
        base_timecode = video_manager.get_base_timecode()
        
        try:
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list(base_timecode)
        finally:
            video_manager.release()
        
        return scene_list
    
    def _extract_keyframes_from_scenes(
        self,
        video_path: str,
        scenes: List,
        fps: float
    ) -> List[Dict]:
        """Extract one keyframe (middle frame) from each scene"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        keyframes = []
        
        for scene_idx, (start_tc, end_tc) in enumerate(scenes):
            start_frame = start_tc.get_frames()
            end_frame = end_tc.get_frames()
            
            # Calculate middle frame
            if end_frame <= start_frame:
                key_frame_num = start_frame
            else:
                mid_offset = (end_frame - start_frame) // 2
                key_frame_num = start_frame + mid_offset
            
            # Extract frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, key_frame_num)
            ret, frame = cap.read()
            
            if not ret or frame is None:
                print(f"   ⚠️  Cannot read frame {key_frame_num} for scene {scene_idx}")
                continue
            
            # Convert to PIL Image
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            timestamp = key_frame_num / fps
            scene_start_time = start_frame / fps
            scene_end_time = end_frame / fps
            scene_duration = scene_end_time - scene_start_time
            
            # Calculate importance (longer scenes = more important)
            max_importance = 1.0
            importance = min(max_importance, scene_duration / 5.0)  # 5s scene = 1.0 importance
            
            keyframes.append({
                "frame_index": int(key_frame_num),
                "timestamp": timestamp,
                "image": pil_image,
                "importance_score": importance,
                "metadata": {
                    "method": "scene",
                    "scene_index": scene_idx,
                    "scene_start": scene_start_time,
                    "scene_end": scene_end_time,
                    "scene_duration": scene_duration,
                    "detector_type": self.detector_type,
                    "threshold": self.threshold
                }
            })
        
        cap.release()
        return keyframes
    
    def _single_keyframe_fallback(self, video_path: str) -> List[Dict]:
        """Fallback: return middle frame of video"""
        cap = cv2.VideoCapture(video_path)
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        mid_frame = total_frames // 2
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
        ret, frame = cap.read()
        
        if not ret:
            cap.release()
            return []
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        
        cap.release()
        
        return [{
            "frame_index": int(mid_frame),
            "timestamp": float(mid_frame / fps),
            "image": pil_image,
            "importance_score": 1.0,
            "metadata": {"method": "single_frame_fallback"}
        }]