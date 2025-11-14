# app/services/keyframe_detectors/base.py
"""
Base class for keyframe detection strategies.
"""
from abc import ABC, abstractmethod
from typing import List, Dict
from PIL import Image


class BaseKeyframeDetector(ABC):
    """
    Abstract base class for keyframe detection.
    """
    
    def __init__(self, **kwargs):
        """Initialize detector with parameters"""
        self.params = kwargs
    
    @abstractmethod
    def detect(self, video_path: str) -> List[Dict]:
        """
        Detect keyframes in video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of keyframe info dictionaries with keys:
            - frame_index: int
            - timestamp: float (seconds)
            - image: PIL.Image
            - importance_score: float (0.0-1.0)
            - metadata: dict (optional, detector-specific info)
        """
        pass
    
    @abstractmethod
    def get_method_name(self) -> str:
        """Get method name for logging"""
        pass
    
    def _get_video_info(self, video_path: str) -> dict:
        """Get basic video information"""
        import cv2
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        info = {
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'fps': cap.get(cv2.CAP_PROP_FPS) or 30,
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        }
        info['duration'] = info['total_frames'] / info['fps']
        
        cap.release()
        return info