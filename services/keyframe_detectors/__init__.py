# app/services/keyframe_detectors/__init__.py
"""
Keyframe detection strategies.
"""
from .base import BaseKeyframeDetector
from .difference_detector import DifferenceKeyframeDetector
from .scene_detector import SceneKeyframeDetector
from .factory import create_keyframe_detector

__all__ = [
    'BaseKeyframeDetector',
    'DifferenceKeyframeDetector',
    'SceneKeyframeDetector',
    'create_keyframe_detector'
]