# app/services/keyframe_detectors/factory.py
"""
Factory for creating keyframe detectors.
"""
from typing import Optional

from .base import BaseKeyframeDetector
from .difference_detector import DifferenceKeyframeDetector
from .scene_detector import SceneKeyframeDetector


def create_keyframe_detector(
    method: str,
    **kwargs
) -> BaseKeyframeDetector:
    """
    Factory function to create keyframe detector.
    
    Args:
        method: Detection method ("difference" or "scene")
        **kwargs: Parameters specific to each detector
        
    Returns:
        BaseKeyframeDetector instance
        
    Raises:
        ValueError: If method is unknown
    """
    if method == "difference":
        return DifferenceKeyframeDetector(
            threshold=kwargs.get('threshold', 0.3),
            min_keyframes=kwargs.get('min_keyframes', 3),
            max_keyframes=kwargs.get('max_keyframes', 8)
        )
    
    elif method == "scene":
        return SceneKeyframeDetector(
            detector_type=kwargs.get('detector_type', 'content'),
            threshold=kwargs.get('threshold', 27.0),
            min_scene_length=kwargs.get('min_scene_length', 1.0)
        )
    
    else:
        raise ValueError(
            f"Unknown keyframe detection method: {method}. "
            f"Supported methods: 'difference', 'scene'"
        )