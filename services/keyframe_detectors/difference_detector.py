# app/services/keyframe_detectors/difference_detector.py
"""
Frame difference-based keyframe detection (original method).
"""
import cv2
import numpy as np
import peakutils
from typing import List, Dict
from PIL import Image

from .base import BaseKeyframeDetector


class DifferenceKeyframeDetector(BaseKeyframeDetector):
    """
    Keyframe detection using frame-to-frame difference analysis.
    Detects peaks in pixel difference magnitude.
    """
    
    def __init__(
        self,
        threshold: float = 0.3,
        min_keyframes: int = 3,
        max_keyframes: int = 8
    ):
        """
        Initialize difference-based detector.
        
        Args:
            threshold: Detection threshold (0.0-1.0)
            min_keyframes: Minimum number of keyframes
            max_keyframes: Maximum number of keyframes (adaptive)
        """
        super().__init__(
            threshold=threshold,
            min_keyframes=min_keyframes,
            max_keyframes=max_keyframes
        )
        self.threshold = threshold
        self.min_keyframes = min_keyframes
        self.base_max_keyframes = max_keyframes
    
    def get_method_name(self) -> str:
        return "Frame Difference Analysis"
    
    def _calculate_adaptive_max(self, duration_sec: float) -> int:
        """Calculate adaptive max keyframes based on duration"""
        if duration_sec < 30:
            return min(15, int(duration_sec / 2))
        elif duration_sec < 120:
            return 12
        elif duration_sec < 300:
            return 10
        elif duration_sec < 600:
            return 8
        else:
            return max(5, int(duration_sec / 120))
    
    def detect(self, video_path: str) -> List[Dict]:
        """
        Detect keyframes using frame difference analysis.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of keyframe info dictionaries
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        duration_sec = total_frames / fps
        
        # Calculate adaptive max
        adaptive_max = self._calculate_adaptive_max(duration_sec)
        
        print(f"\n🔍 DIFFERENCE-BASED KEYFRAME DETECTION")
        print(f"{'='*70}")
        print(f"   Video: {duration_sec:.1f}s ({total_frames} frames @ {fps:.1f} fps)")
        print(f"   Adaptive Strategy: max {adaptive_max} keyframes")
        print(f"   Threshold: {self.threshold}")
        print(f"{'='*70}")
        
        # For very short videos, use uniform sampling
        if duration_sec < 10:
            print(f"⚡ Short video detected, using uniform sampling")
            cap.release()
            return self._uniform_sampling(video_path, min(5, adaptive_max))
        
        # Frame difference analysis
        lstdiff_mag = []
        frames = []
        last_frame = None
        
        print(f"📊 Analyzing frame differences...")
        
        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to grayscale and blur
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (9, 9), 0.0)
            
            frames.append(frame)
            
            if i == 0:
                last_frame = gray
                lstdiff_mag.append(0)
                continue
            
            # Calculate difference
            diff = cv2.subtract(gray, last_frame)
            diff_mag = cv2.countNonZero(diff)
            lstdiff_mag.append(diff_mag)
            
            last_frame = gray
            
            # Progress indicator
            if i % 100 == 0:
                progress = (i / total_frames) * 100
                print(f"   Progress: {progress:.1f}% ({i}/{total_frames} frames)", end='\r')
        
        cap.release()
        print()  # New line after progress
        
        if len(lstdiff_mag) < self.min_keyframes:
            print(f"⚠️  Not enough frames for peak detection")
            return []
        
        # Find peaks
        y = np.array(lstdiff_mag)
        base = peakutils.baseline(y, 2)
        
        # Try different thresholds if needed
        indices = []
        current_threshold = self.threshold
        
        for attempt in range(3):
            indices = peakutils.indexes(y - base, current_threshold, min_dist=int(fps * 2))
            
            if len(indices) >= self.min_keyframes:
                break
            
            current_threshold *= 0.7
            print(f"   Retry with threshold {current_threshold:.2f}")
        
        if len(indices) < self.min_keyframes:
            print(f"⚠️  Only {len(indices)} peaks found, fallback to uniform")
            return self._uniform_sampling(video_path, adaptive_max)
        
        # Limit to adaptive max
        if len(indices) > adaptive_max:
            ranked_indices = sorted(
                indices,
                key=lambda i: lstdiff_mag[i],
                reverse=True
            )[:adaptive_max]
            indices = sorted(ranked_indices)
        
        # Extract keyframes
        keyframes = []
        max_diff = max(lstdiff_mag)
        
        print(f"\n✅ Peak Detection Complete:")
        print(f"   Peaks Found: {len(indices)}")
        print(f"   Selected Keyframes: {len(indices)}")
        
        for idx in indices:
            frame = frames[idx]
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            timestamp = float(idx / fps)
            diff_magnitude = lstdiff_mag[idx]
            importance = diff_magnitude / max_diff
            
            keyframes.append({
                "frame_index": int(idx),
                "timestamp": timestamp,
                "image": pil_image,
                "importance_score": importance,
                "metadata": {
                    "method": "difference",
                    "diff_magnitude": diff_magnitude,
                    "threshold_used": current_threshold
                }
            })
        
        print(f"{'='*70}\n")
        
        return keyframes
    
    def _uniform_sampling(self, video_path: str, num_frames: int) -> List[Dict]:
        """Fallback: uniform sampling"""
        cap = cv2.VideoCapture(video_path)
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
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
                "importance_score": 0.5,
                "metadata": {"method": "uniform_fallback"}
            })
            
            if len(keyframes) >= num_frames:
                break
        
        cap.release()
        return keyframes