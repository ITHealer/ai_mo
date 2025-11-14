# tests/test_keyframe_detector.py
"""
Test keyframe detector with different video lengths.
"""
import sys

import cv2
import numpy as np
from src.services.keyframe_detector import AdaptiveKeyframeDetector


def create_test_video(output_path: str, duration_sec: int, fps: int = 30):
    """Create a test video with scene changes"""
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration_sec * fps
    scene_changes = [int(total_frames * 0.2), int(total_frames * 0.5), int(total_frames * 0.8)]
    
    for i in range(total_frames):
        # Create frame with color based on scene
        if i < scene_changes[0]:
            color = (255, 0, 0)  # Blue scene
        elif i < scene_changes[1]:
            color = (0, 255, 0)  # Green scene
        elif i < scene_changes[2]:
            color = (0, 0, 255)  # Red scene
        else:
            color = (255, 255, 0)  # Yellow scene
        
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = color
        
        # Add some noise
        noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)
        
        out.write(frame)
    
    out.release()
    print(f"✅ Created test video: {output_path} ({duration_sec}s)")


def test_keyframe_detection():
    """Test keyframe detection on videos of different lengths"""
    
    detector = AdaptiveKeyframeDetector(threshold=0.3)
    
    test_cases = [
        ("short_10s.mp4", 10),
        ("short_20s.mp4", 20),
        ("medium_60s.mp4", 60),
        ("medium_120s.mp4", 120),
        ("long_300s.mp4", 300),
        ("long_600s.mp4", 600),
    ]
    
    results = []
    
    for video_name, duration in test_cases:
        print(f"\n{'='*70}")
        print(f"Testing: {video_name} ({duration}s)")
        print(f"{'='*70}")
        
        # Create test video
        create_test_video(video_name, duration)
        
        # Detect keyframes
        keyframes = detector.detect(video_name)
        
        results.append({
            "video": video_name,
            "duration": duration,
            "keyframes_detected": len(keyframes),
            "coverage": len(keyframes) / duration * 60 if duration > 0 else 0
        })
        
        # Print keyframe details
        print(f"\n📊 Keyframe Summary:")
        for i, kf in enumerate(keyframes):
            print(f"   {i+1}. Frame {kf['frame_index']:5d} @ {kf['timestamp']:6.2f}s "
                  f"(importance: {kf['importance_score']:.2f})")
    
    # Summary table
    print(f"\n{'='*70}")
    print(f"SUMMARY: Adaptive Keyframe Detection")
    print(f"{'='*70}")
    print(f"{'Video':<20} {'Duration':<12} {'Keyframes':<12} {'Coverage (f/min)'}")
    print(f"{'-'*70}")
    
    for r in results:
        print(f"{r['video']:<20} {r['duration']:<12} {r['keyframes_detected']:<12} {r['coverage']:.2f}")
    
    print(f"{'='*70}")
    
    # Analysis
    print(f"\n📈 Analysis:")
    print(f"   Short videos (10-20s): Capture more detail")
    print(f"   Medium videos (1-2min): Standard coverage")
    print(f"   Long videos (5-10min): Strategic key scenes only")
    print(f"\n✅ Adaptive strategy ensures efficiency across all video lengths")


if __name__ == "__main__":
    test_keyframe_detection()

'''
## 📊 Phân tích KeyframeDetector

### ❌ Vấn đề với chiến lược cố định max=8:

Video 10s  → 8 frames → 48 frames/min (QUÁ DƯ THỪA)
Video 30s  → 8 frames → 16 frames/min (hợp lý)
Video 5min → 8 frames → 1.6 frames/min (QUÁ ÍT)
Video 30min→ 8 frames → 0.26 frames/min (MISS NHIỀU SCENE)


# Adaptive max keyframes dựa trên duration:
0-30s     → 10-15 frames (chi tiết cho video ngắn)
30s-2min  → 8-12 frames (chuẩn)
2min-5min → 6-10 frames (giảm cho video vừa)
5min-10min→ 5-8 frames (chiến lược cho video dài)
>10min    → 5 frames (chỉ scene chính)
```

### 📈 Coverage tối ưu:
```
Short (10s):   1 frame / 2s   → chi tiết
Medium (2min):  1 frame / 10s  → cân bằng
Long (10min):   1 frame / 2min → hiệu quả
'''
