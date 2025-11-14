# # app/utils/keyframe_storage.py
# """
# Utilities for saving keyframes to organized folder structure.
# """
# import os
# from datetime import datetime
# from pathlib import Path
# from typing import List, Dict, Optional
# from PIL import Image


# class KeyframeStorage:
#     """
#     Manages storage of keyframes in organized folder structure.
#     """
    
#     def __init__(self, base_dir: str = "./output/keyframes"):
#         """
#         Initialize storage manager.
        
#         Args:
#             base_dir: Base directory for all keyframe runs
#         """
#         self.base_dir = Path(base_dir)
#         self.base_dir.mkdir(parents=True, exist_ok=True)
    
#     def create_run_folder(
#         self,
#         job_id: Optional[str] = None,
#         method: str = "keyframe",
#         video_name: Optional[str] = None
#     ) -> Path:
#         """
#         Create unique folder for this run.
        
#         Args:
#             job_id: Job ID for identification
#             method: Detection method name
#             video_name: Original video filename
            
#         Returns:
#             Path to created folder
#         """
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
#         if job_id:
#             folder_name = f"{job_id[:8]}_{method}_{timestamp}"
#         elif video_name:
#             folder_name = f"{video_name}_{method}_{timestamp}"
#         else:
#             folder_name = f"{method}_{timestamp}"
        
#         run_folder = self.base_dir / folder_name
#         run_folder.mkdir(parents=True, exist_ok=True)
        
#         return run_folder
    
#     def save_keyframes(
#         self,
#         keyframes: List[Dict],
#         run_folder: Path,
#         video_name: str = "video"
#     ) -> List[str]:
#         """
#         Save keyframes to folder.
        
#         Args:
#             keyframes: List of keyframe dictionaries
#             run_folder: Folder to save to
#             video_name: Base name for files
            
#         Returns:
#             List of saved file paths
#         """
#         saved_paths = []
        
#         print(f"\n💾 SAVING KEYFRAMES")
#         print(f"{'='*70}")
#         print(f"   Destination: {run_folder}")
#         print(f"   Keyframes: {len(keyframes)}")
#         print(f"{'='*70}")
        
#         for i, kf in enumerate(keyframes):
#             image: Image.Image = kf["image"]
#             timestamp = kf["timestamp"]
#             frame_idx = kf["frame_index"]
#             importance = kf["importance_score"]
            
#             # Build filename with metadata
#             method = kf.get("metadata", {}).get("method", "unknown")
            
#             filename = (
#                 f"{video_name}_kf{i+1:03d}_"
#                 f"f{frame_idx:06d}_"
#                 f"t{timestamp:.2f}s_"
#                 f"imp{importance:.2f}_"
#                 f"{method}.jpg"
#             )
            
#             filepath = run_folder / filename
            
#             try:
#                 image.save(filepath, quality=95)
#                 saved_paths.append(str(filepath))
                
#                 if i == 0 or i == len(keyframes) - 1 or i % 10 == 0:
#                     print(f"   [{i+1:3d}/{len(keyframes)}] {filename}")
                
#             except Exception as e:
#                 print(f"   ❌ Failed to save {filename}: {e}")
        
#         print(f"\n✅ Saved {len(saved_paths)}/{len(keyframes)} keyframes")
#         print(f"{'='*70}\n")
        
#         # Save metadata file
#         self._save_metadata(keyframes, run_folder)
        
#         return saved_paths
    
#     def _save_metadata(self, keyframes: List[Dict], run_folder: Path):
#         """Save metadata file with keyframe information"""
#         import json
        
#         metadata = {
#             "total_keyframes": len(keyframes),
#             "saved_at": datetime.now().isoformat(),
#             "keyframes": [
#                 {
#                     "index": i,
#                     "frame_index": kf["frame_index"],
#                     "timestamp": kf["timestamp"],
#                     "importance_score": kf["importance_score"],
#                     "metadata": kf.get("metadata", {})
#                 }
#                 for i, kf in enumerate(keyframes)
#             ]
#         }
        
#         metadata_file = run_folder / "metadata.json"
        
#         try:
#             with open(metadata_file, 'w', encoding='utf-8') as f:
#                 json.dump(metadata, f, indent=2, ensure_ascii=False)
#             print(f"   📄 Metadata saved: {metadata_file.name}")
#         except Exception as e:
#             print(f"   ⚠️  Failed to save metadata: {e}")


# app/utils/keyframe_storage.py (Enhanced with category organization)
"""
Utilities for saving keyframes with moderation results.
"""
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageFont


class KeyframeStorage:
    """
    Manages storage of keyframes with moderation results.
    """
    
    def __init__(
        self,
        base_dir: str = "./output/keyframes",
        organize_by_category: bool = True,
        include_safe: bool = True
    ):
        """
        Initialize storage manager.
        
        Args:
            base_dir: Base directory for all keyframe runs
            organize_by_category: Create subfolders for each category
            include_safe: Save safe images (if False, only save violations)
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.organize_by_category = organize_by_category
        self.include_safe = include_safe
    
    def create_run_folder(
        self,
        job_id: Optional[str] = None,
        method: str = "keyframe",
        video_name: Optional[str] = None
    ) -> Path:
        """
        Create unique folder for this run.
        
        Args:
            job_id: Job ID for identification
            method: Detection method name
            video_name: Original video filename
            
        Returns:
            Path to created folder
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if job_id:
            folder_name = f"{job_id[:8]}_{method}_{timestamp}"
        elif video_name:
            folder_name = f"{video_name}_{method}_{timestamp}"
        else:
            folder_name = f"{method}_{timestamp}"
        
        run_folder = self.base_dir / folder_name
        run_folder.mkdir(parents=True, exist_ok=True)
        
        # Create category subfolders if enabled
        if self.organize_by_category:
            categories = [
                "safe", "violence_threats", "sexual_explicit", "dangerous",
                "criminal", "gore", "obscene", "self_harm", 
                "hate_discrimination", "illegal"
            ]
            for category in categories:
                (run_folder / category).mkdir(exist_ok=True)
        
        return run_folder
    
    def save_keyframes_with_results(
        self,
        keyframes: List[Dict],
        moderation_results: List[Dict],
        run_folder: Path,
        video_name: str = "video"
    ) -> Dict[str, List[str]]:
        """
        Save keyframes with moderation results organized by category.
        
        Args:
            keyframes: List of keyframe dictionaries
            moderation_results: List of moderation result dictionaries
            run_folder: Folder to save to
            video_name: Base name for files
            
        Returns:
            Dictionary mapping category to list of saved file paths
        """
        saved_by_category = {}
        stats = {
            "total": len(keyframes),
            "saved": 0,
            "skipped_safe": 0,
            "by_category": {}
        }
        
        print(f"\n💾 SAVING KEYFRAMES WITH MODERATION RESULTS")
        print(f"{'='*70}")
        print(f"   Destination: {run_folder}")
        print(f"   Total Keyframes: {len(keyframes)}")
        print(f"   Organization: {'By Category' if self.organize_by_category else 'Flat'}")
        print(f"   Include Safe: {self.include_safe}")
        print(f"{'='*70}")
        
        for i, (kf, result) in enumerate(zip(keyframes, moderation_results)):
            category_code = result.get("category_code", "safe")
            category_name = result.get("category", "Safe")
            confidence = result.get("confidence", 0.0)
            
            # Skip safe images if configured
            if not self.include_safe and category_code == "safe":
                stats["skipped_safe"] += 1
                continue
            
            # Track stats
            if category_code not in stats["by_category"]:
                stats["by_category"][category_code] = 0
            stats["by_category"][category_code] += 1
            
            # Get image and metadata
            image: Image.Image = kf["image"]
            timestamp = kf["timestamp"]
            frame_idx = kf["frame_index"]
            importance = kf["importance_score"]
            method = kf.get("metadata", {}).get("method", "unknown")
            
            # Build filename with category and result
            category_prefix = category_code.upper() if category_code != "safe" else "SAFE"
            confidence_str = f"{confidence:.0%}" if confidence > 0 else "N/A"
            
            filename = (
                f"{category_prefix}_"
                f"conf{confidence_str}_"
                f"kf{i+1:03d}_"
                f"f{frame_idx:06d}_"
                f"t{timestamp:.2f}s_"
                f"imp{importance:.2f}_"
                f"{method}.jpg"
            )
            
            # Determine save path
            if self.organize_by_category:
                category_folder = run_folder / category_code
                filepath = category_folder / filename
            else:
                filepath = run_folder / filename
            
            try:
                # Add visual overlay with moderation result
                image_with_overlay = self._add_overlay(
                    image.copy(),
                    category_name,
                    confidence,
                    timestamp
                )
                
                # Save image
                image_with_overlay.save(filepath, quality=95)
                
                # Track saved paths
                if category_code not in saved_by_category:
                    saved_by_category[category_code] = []
                saved_by_category[category_code].append(str(filepath))
                
                stats["saved"] += 1
                
                # Log progress
                status_icon = "✅" if category_code == "safe" else "⚠️ "
                if i == 0 or i == len(keyframes) - 1 or i % 10 == 0:
                    print(f"   [{i+1:3d}/{len(keyframes)}] {status_icon} {category_prefix:20s} {filename}")
                
            except Exception as e:
                print(f"   ❌ Failed to save {filename}: {e}")
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"📊 SAVE SUMMARY")
        print(f"{'='*70}")
        print(f"   Total Keyframes: {stats['total']}")
        print(f"   Saved: {stats['saved']}")
        if not self.include_safe:
            print(f"   Skipped (Safe): {stats['skipped_safe']}")
        
        print(f"\n   By Category:")
        for category, count in sorted(stats["by_category"].items()):
            icon = "⚠️ " if category != "safe" else "✅"
            print(f"      {icon} {category:20s}: {count:3d} images")
        
        print(f"{'='*70}\n")
        
        # Save metadata and summary reports
        self._save_detailed_metadata(
            keyframes=keyframes,
            moderation_results=moderation_results,
            run_folder=run_folder,
            stats=stats
        )
        
        self._create_summary_report(
            run_folder=run_folder,
            stats=stats,
            saved_by_category=saved_by_category
        )
        
        return saved_by_category
    
    def _add_overlay(
        self,
        image: Image.Image,
        category: str,
        confidence: float,
        timestamp: float
    ) -> Image.Image:
        """
        Add visual overlay with moderation result.
        
        Args:
            image: Original image
            category: Moderation category
            confidence: Confidence score
            timestamp: Frame timestamp
            
        Returns:
            Image with overlay
        """
        try:
            draw = ImageDraw.Draw(image)
            
            # Color coding
            color_map = {
                "safe": (0, 200, 0),  # Green
                "violence_threats": (255, 0, 0),  # Red
                "sexual_explicit": (255, 0, 255),  # Magenta
                "dangerous": (255, 140, 0),  # Orange
                "criminal": (139, 0, 0),  # Dark red
                "gore": (128, 0, 0),  # Maroon
                "obscene": (255, 165, 0),  # Orange
                "self_harm": (255, 69, 0),  # Red-orange
                "hate_discrimination": (178, 34, 34),  # Firebrick
                "illegal": (139, 0, 0)  # Dark red
            }
            
            # Determine color
            category_code = category.lower().replace(" & ", "_").replace(" ", "_")
            color = color_map.get(category_code, (128, 128, 128))
            
            # Draw banner at top
            banner_height = 40
            draw.rectangle(
                [(0, 0), (image.width, banner_height)],
                fill=(0, 0, 0, 180)
            )
            
            # Add text
            text = f"{category.upper()} ({confidence:.0%}) | {timestamp:.2f}s"
            
            try:
                # Try to use a better font if available
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position (centered)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (image.width - text_width) // 2
            
            # Draw text with outline for better visibility
            outline_color = (0, 0, 0)
            for adj_x, adj_y in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                draw.text((text_x+adj_x, 8+adj_y), text, font=font, fill=outline_color)
            
            draw.text((text_x, 8), text, font=font, fill=color)
            
            # Draw color bar at bottom
            bar_height = 10
            draw.rectangle(
                [(0, image.height - bar_height), (image.width, image.height)],
                fill=color
            )
            
            return image
            
        except Exception as e:
            print(f"   ⚠️  Failed to add overlay: {e}")
            return image
    
    def _save_detailed_metadata(
        self,
        keyframes: List[Dict],
        moderation_results: List[Dict],
        run_folder: Path,
        stats: Dict
    ):
        """Save detailed metadata JSON file"""
        import json
        
        metadata = {
            "saved_at": datetime.now().isoformat(),
            "total_keyframes": stats["total"],
            "saved_keyframes": stats["saved"],
            "skipped_safe": stats.get("skipped_safe", 0),
            "statistics": stats["by_category"],
            "keyframes": []
        }
        
        for i, (kf, result) in enumerate(zip(keyframes, moderation_results)):
            metadata["keyframes"].append({
                "index": i,
                "frame_index": kf["frame_index"],
                "timestamp": kf["timestamp"],
                "importance_score": kf["importance_score"],
                "moderation": {
                    "category": result.get("category", "Safe"),
                    "category_code": result.get("category_code", "safe"),
                    "confidence": result.get("confidence", 0.0),
                    "reasoning": result.get("reasoning", "N/A")
                },
                "metadata": kf.get("metadata", {})
            })
        
        metadata_file = run_folder / "moderation_metadata.json"
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"   📄 Metadata saved: {metadata_file.name}")
        except Exception as e:
            print(f"   ⚠️  Failed to save metadata: {e}")
    
    def _create_summary_report(
        self,
        run_folder: Path,
        stats: Dict,
        saved_by_category: Dict[str, List[str]]
    ):
        """Create human-readable summary report"""
        report_file = run_folder / "SUMMARY_REPORT.txt"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write("VIDEO MODERATION KEYFRAME SUMMARY\n")
                f.write("="*70 + "\n\n")
                
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Location: {run_folder}\n\n")
                
                f.write("-"*70 + "\n")
                f.write("STATISTICS\n")
                f.write("-"*70 + "\n")
                f.write(f"Total Keyframes: {stats['total']}\n")
                f.write(f"Saved: {stats['saved']}\n")
                if "skipped_safe" in stats:
                    f.write(f"Skipped (Safe): {stats['skipped_safe']}\n")
                f.write("\n")
                
                f.write("-"*70 + "\n")
                f.write("VIOLATIONS DETECTED\n")
                f.write("-"*70 + "\n")
                
                violations = {k: v for k, v in stats["by_category"].items() if k != "safe"}
                safe_count = stats["by_category"].get("safe", 0)
                
                if violations:
                    f.write("\n⚠️  VIOLATIONS FOUND:\n\n")
                    for category, count in sorted(violations.items(), key=lambda x: x[1], reverse=True):
                        f.write(f"   {category.upper():25s}: {count:3d} images\n")
                        
                        # List files in this category
                        if category in saved_by_category:
                            f.write(f"      Files:\n")
                            for filepath in saved_by_category[category][:5]:  # Show first 5
                                filename = Path(filepath).name
                                f.write(f"         - {filename}\n")
                            if len(saved_by_category[category]) > 5:
                                f.write(f"         ... and {len(saved_by_category[category]) - 5} more\n")
                        f.write("\n")
                else:
                    f.write("\n✅ NO VIOLATIONS DETECTED\n\n")
                
                f.write(f"Safe Images: {safe_count}\n\n")
                
                f.write("-"*70 + "\n")
                f.write("FOLDER STRUCTURE\n")
                f.write("-"*70 + "\n\n")
                
                f.write(f"Root: {run_folder.name}/\n")
                for category, paths in sorted(saved_by_category.items()):
                    f.write(f"   {category}/  ({len(paths)} images)\n")
                
                f.write("\n" + "="*70 + "\n")
            
            print(f"   📄 Summary report saved: {report_file.name}")
            
        except Exception as e:
            print(f"   ⚠️  Failed to create summary report: {e}")
    
    def save_keyframes(
        self,
        keyframes: List[Dict],
        run_folder: Path,
        video_name: str = "video"
    ) -> List[str]:
        """
        Legacy method - save keyframes without moderation results.
        """
        saved_paths = []
        
        print(f"\n💾 SAVING KEYFRAMES")
        print(f"{'='*70}")
        print(f"   Destination: {run_folder}")
        print(f"   Keyframes: {len(keyframes)}")
        print(f"{'='*70}")
        
        for i, kf in enumerate(keyframes):
            image: Image.Image = kf["image"]
            timestamp = kf["timestamp"]
            frame_idx = kf["frame_index"]
            importance = kf["importance_score"]
            method = kf.get("metadata", {}).get("method", "unknown")
            
            filename = (
                f"{video_name}_kf{i+1:03d}_"
                f"f{frame_idx:06d}_"
                f"t{timestamp:.2f}s_"
                f"imp{importance:.2f}_"
                f"{method}.jpg"
            )
            
            filepath = run_folder / filename
            
            try:
                image.save(filepath, quality=95)
                saved_paths.append(str(filepath))
                
                if i == 0 or i == len(keyframes) - 1 or i % 10 == 0:
                    print(f"   [{i+1:3d}/{len(keyframes)}] {filename}")
                
            except Exception as e:
                print(f"   ❌ Failed to save {filename}: {e}")
        
        print(f"\n✅ Saved {len(saved_paths)}/{len(keyframes)} keyframes")
        print(f"{'='*70}\n")
        
        return saved_paths