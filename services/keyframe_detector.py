# # app/services/keyframe_detector.py
# """
# Keyframe detection service.
# """
# import os
# import cv2
# import numpy as np
# import peakutils
# from typing import List, Dict
# from PIL import Image


# class KeyframeDetector:
#     """
#     Keyframe detection using frame difference analysis.
#     Based on: https://github.com/joelibaceta/video-keyframe-detector
#     """
    
#     def __init__(
#         self,
#         threshold: float = 0.3,
#         max_keyframes: int = 8
#     ):
#         """
#         Initialize keyframe detector.
        
#         Args:
#             threshold: Detection threshold (0.0-1.0)
#             max_keyframes: Maximum number of keyframes to extract
#         """
#         self.threshold = threshold
#         self.max_keyframes = max_keyframes
    
#     def detect(self, video_path: str) -> List[Dict]:
#         """
#         Detect keyframes in video.
        
#         Args:
#             video_path: Path to video file
            
#         Returns:
#             List of keyframe info: [{"frame_index": int, "timestamp": float, "image": PIL.Image}, ...]
#         """
#         cap = cv2.VideoCapture(video_path)
        
#         if not cap.isOpened():
#             raise ValueError(f"Failed to open video: {video_path}")
        
#         length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#         fps = cap.get(cv2.CAP_PROP_FPS) or 30
        
#         lstdiff_mag = []
#         frames = []
#         last_frame = None
        
#         print(f"🔍 Analyzing {length} frames for keyframe detection...")
        
#         for i in range(length):
#             ret, frame = cap.read()
#             if not ret:
#                 break
            
#             # Convert to grayscale
#             gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#             gray = cv2.GaussianBlur(gray, (9, 9), 0.0)
            
#             frames.append(frame)
            
#             if i == 0:
#                 last_frame = gray
#                 lstdiff_mag.append(0)
#                 continue
            
#             # Calculate difference
#             diff = cv2.subtract(gray, last_frame)
#             diff_mag = cv2.countNonZero(diff)
#             lstdiff_mag.append(diff_mag)
            
#             last_frame = gray
        
#         cap.release()
        
#         if len(lstdiff_mag) < 3:
#             print("⚠️  Not enough frames for keyframe detection")
#             return []
        
#         # Find peaks
#         y = np.array(lstdiff_mag)
#         base = peakutils.baseline(y, 2)
#         indices = peakutils.indexes(y - base, self.threshold, min_dist=1)
        
#         # Limit to max_keyframes
#         if len(indices) > self.max_keyframes:
#             ranked_indices = sorted(
#                 indices,
#                 key=lambda i: lstdiff_mag[i],
#                 reverse=True
#             )[:self.max_keyframes]
#             indices = sorted(ranked_indices)
        
#         # Extract keyframes
#         keyframes = []
#         for idx in indices:
#             frame = frames[idx]
#             rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             pil_image = Image.fromarray(rgb_frame)
            
#             keyframes.append({
#                 "frame_index": int(idx),
#                 "timestamp": float(idx / fps),
#                 "image": pil_image
#             })
        
#         print(f"✅ Detected {len(keyframes)} keyframes")
#         return keyframes



# app/services/keyframe_detector.py (Improved with adaptive strategy)
"""
Adaptive keyframe detection service.
"""
import os
import cv2
import numpy as np
import peakutils
from typing import List, Dict
from PIL import Image


class AdaptiveKeyframeDetector:
    """
    Adaptive keyframe detection with dynamic strategy based on video duration.
    
    Strategy:
    - Short videos (<30s): More frames (max 10-15)
    - Medium videos (30s-5min): Standard (max 8-12)
    - Long videos (>5min): Strategic sampling (max 5-8)
    """
    
    def __init__(
        self,
        threshold: float = 0.3,
        min_keyframes: int = 3,
        max_keyframes: int = 8
    ):
        """
        Initialize adaptive keyframe detector.
        
        Args:
            threshold: Detection threshold (0.0-1.0)
            min_keyframes: Minimum number of keyframes
            max_keyframes: Maximum number of keyframes (will adapt based on duration)
        """
        self.threshold = threshold
        self.min_keyframes = min_keyframes
        self.base_max_keyframes = max_keyframes
    
    def _calculate_adaptive_max(self, duration_sec: float) -> int:
        """
        Calculate adaptive max keyframes based on video duration.
        
        Strategy:
        - 0-30s: 10-15 frames (capture more detail in short videos)
        - 30s-2min: 8-12 frames (standard)
        - 2min-5min: 6-10 frames (reduce for medium videos)
        - 5min-10min: 5-8 frames (strategic for long videos)
        - >10min: 5 frames minimum (only key scenes)
        
        Args:
            duration_sec: Video duration in seconds
            
        Returns:
            Adaptive max keyframes count
        """
        if duration_sec < 30:
            # Short video: more frames for detail
            return min(15, int(duration_sec / 2))  # ~1 frame per 2 seconds
        elif duration_sec < 120:  # 2 minutes
            # Standard video
            return 12
        elif duration_sec < 300:  # 5 minutes
            # Medium video
            return 10
        elif duration_sec < 600:  # 10 minutes
            # Long video
            return 8
        else:
            # Very long video: only key scenes
            return max(5, int(duration_sec / 120))  # ~1 frame per 2 minutes
    
    def detect(self, video_path: str) -> List[Dict]:
        """
        Detect keyframes in video with adaptive strategy.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of keyframe info with metadata
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        duration_sec = total_frames / fps
        
        # Calculate adaptive max keyframes
        adaptive_max = self._calculate_adaptive_max(duration_sec)
        
        print(f"🎬 Video: {duration_sec:.1f}s ({total_frames} frames @ {fps:.1f} fps)")
        print(f"🔍 Adaptive strategy: max {adaptive_max} keyframes")
        
        # For very short videos, use uniform sampling
        if duration_sec < 10:
            print(f"⚡ Short video detected, using uniform sampling")
            return self._uniform_sampling(cap, total_frames, fps, min(5, adaptive_max))
        
        # Frame difference analysis
        lstdiff_mag = []
        frames = []
        last_frame = None
        
        print(f"📊 Analyzing {total_frames} frames...")
        
        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (9, 9), 0.0)
            
            frames.append(frame)
            
            if i == 0:
                last_frame = gray
                lstdiff_mag.append(0)
                continue
            
            diff = cv2.subtract(gray, last_frame)
            diff_mag = cv2.countNonZero(diff)
            lstdiff_mag.append(diff_mag)
            
            last_frame = gray
        
        cap.release()
        
        if len(lstdiff_mag) < self.min_keyframes:
            print(f"⚠️  Not enough frames for keyframe detection")
            return []
        
        # Find peaks with adaptive threshold
        y = np.array(lstdiff_mag)
        base = peakutils.baseline(y, 2)
        
        # Try different thresholds if not enough keyframes found
        indices = []
        current_threshold = self.threshold
        
        for attempt in range(3):
            indices = peakutils.indexes(y - base, current_threshold, min_dist=int(fps * 2))
            
            if len(indices) >= self.min_keyframes:
                break
            
            # Reduce threshold for next attempt
            current_threshold *= 0.7
            print(f"   Retry with threshold {current_threshold:.2f}")
        
        if len(indices) < self.min_keyframes:
            print(f"⚠️  Only {len(indices)} keyframes found, falling back to uniform sampling")
            cap = cv2.VideoCapture(video_path)
            result = self._uniform_sampling(cap, total_frames, fps, adaptive_max)
            cap.release()
            return result
        
        # Limit to adaptive max
        if len(indices) > adaptive_max:
            # Rank by difference magnitude and take top N
            ranked_indices = sorted(
                indices,
                key=lambda i: lstdiff_mag[i],
                reverse=True
            )[:adaptive_max]
            indices = sorted(ranked_indices)
        
        # Extract keyframes with metadata
        keyframes = []
        for idx in indices:
            frame = frames[idx]
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            timestamp = float(idx / fps)
            diff_magnitude = lstdiff_mag[idx]
            
            keyframes.append({
                "frame_index": int(idx),
                "timestamp": timestamp,
                "image": pil_image,
                "diff_magnitude": diff_magnitude,
                "importance_score": diff_magnitude / max(lstdiff_mag)
            })
        
        print(f"✅ Detected {len(keyframes)} keyframes (adaptive max: {adaptive_max})")
        print(f"   Coverage: {len(keyframes)/duration_sec*60:.1f} frames/minute")
        
        return keyframes
    
    def _uniform_sampling(
        self,
        cap: cv2.VideoCapture,
        total_frames: int,
        fps: float,
        num_frames: int
    ) -> List[Dict]:
        """
        Fallback: uniform sampling when keyframe detection fails.
        
        Args:
            cap: Video capture object
            total_frames: Total number of frames
            fps: Frames per second
            num_frames: Number of frames to sample
            
        Returns:
            List of uniformly sampled frames
        """
        interval = max(1, total_frames // num_frames)
        keyframes = []
        
        for i in range(0, total_frames, interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            keyframes.append({
                "frame_index": int(i),
                "timestamp": float(i / fps),
                "image": pil_image,
                "diff_magnitude": 0,
                "importance_score": 0.5
            })
            
            if len(keyframes) >= num_frames:
                break
        
        return keyframes


class KeyframeDetector(AdaptiveKeyframeDetector):
    """Alias for backward compatibility"""
    pass