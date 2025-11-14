# # # # app/core/workers.py
# # # """
# # # Worker threads for processing moderation tasks.
# # # """
# # # import threading
# # # import time
# # # from typing import List
# # # from PIL import Image

# # # from src.services.text_moderation import TextModerationService
# # # from src.services.image_moderation import ImageModerationService
# # # from src.services.video_moderation import VideoModerationService
# # # from src.core.queue_system import QueueSystem, Task, TaskType
# # # from src.core.job_manager import JobManager, JobStatus


# # # class BaseWorker(threading.Thread):
# # #     """Base worker thread"""
    
# # #     def __init__(
# # #         self,
# # #         worker_id: int,
# # #         queue_system: QueueSystem,
# # #         job_manager: JobManager,
# # #         task_type: TaskType
# # #     ):
# # #         super().__init__(daemon=True)
# # #         self.worker_id = worker_id
# # #         self.queue_system = queue_system
# # #         self.job_manager = job_manager
# # #         self.task_type = task_type
# # #         self.running = False
# # #         self.name = f"{task_type.value}-worker-{worker_id}"
    
# # #     def run(self):
# # #         """Worker main loop"""
# # #         self.running = True
# # #         print(f"✅ {self.name} started")
        
# # #         while self.running:
# # #             try:
# # #                 task = self.queue_system.get_task(self.task_type, timeout=1.0)
                
# # #                 if task:
# # #                     self.process_task(task)
# # #                     self.queue_system.mark_done(task)
                    
# # #             except Exception as e:
# # #                 print(f"❌ {self.name} error: {e}")
# # #                 if task:
# # #                     self.job_manager.set_error(task.job_id, str(e))
# # #                     self.queue_system.mark_failed(self.task_type)
        
# # #         print(f"🔴 {self.name} stopped")
    
# # #     def process_task(self, task: Task):
# # #         """Override in subclass"""
# # #         raise NotImplementedError
    
# # #     def stop(self):
# # #         """Stop worker"""
# # #         self.running = False


# # # class TextWorker(BaseWorker):
# # #     """Worker for text moderation"""
    
# # #     def __init__(
# # #         self,
# # #         worker_id: int,
# # #         queue_system: QueueSystem,
# # #         job_manager: JobManager,
# # #         text_service: TextModerationService
# # #     ):
# # #         super().__init__(worker_id, queue_system, job_manager, TaskType.TEXT)
# # #         self.text_service = text_service
    
# # #     def process_task(self, task: Task):
# # #         """Process text moderation task"""
# # #         self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
# # #         try:
# # #             result = self.text_service.moderate(task.data)
# # #             self.job_manager.set_result(task.job_id, result.model_dump())
# # #             self.queue_system.mark_completed(TaskType.TEXT)
            
# # #             if task.callback:
# # #                 task.callback(result)
                
# # #         except Exception as e:
# # #             self.job_manager.set_error(task.job_id, str(e))
# # #             self.queue_system.mark_failed(TaskType.TEXT)
# # #             raise


# # # class ImageWorker(BaseWorker):
# # #     """Worker for image moderation"""
    
# # #     def __init__(
# # #         self,
# # #         worker_id: int,
# # #         queue_system: QueueSystem,
# # #         job_manager: JobManager,
# # #         image_service: ImageModerationService
# # #     ):
# # #         super().__init__(worker_id, queue_system, job_manager, TaskType.IMAGE)
# # #         self.image_service = image_service
    
# # #     def process_task(self, task: Task):
# # #         """Process image moderation task"""
# # #         self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
# # #         try:
# # #             image: Image.Image = task.data
# # #             result = self.image_service.moderate(image)
# # #             self.job_manager.set_result(task.job_id, result.model_dump())
# # #             self.queue_system.mark_completed(TaskType.IMAGE)
            
# # #             if task.callback:
# # #                 task.callback(result)
                
# # #         except Exception as e:
# # #             self.job_manager.set_error(task.job_id, str(e))
# # #             self.queue_system.mark_failed(TaskType.IMAGE)
# # #             raise


# # # class VideoWorker(BaseWorker):
# # #     """Worker for video moderation"""
    
# # #     def __init__(
# # #         self,
# # #         worker_id: int,
# # #         queue_system: QueueSystem,
# # #         job_manager: JobManager,
# # #         video_service: VideoModerationService
# # #     ):
# # #         super().__init__(worker_id, queue_system, job_manager, TaskType.VIDEO)
# # #         self.video_service = video_service
    
# # #     def process_task(self, task: Task):
# # #         """Process video moderation task"""
# # #         self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
# # #         try:
# # #             video_path, sampling_fps = task.data
            
# # #             # Update progress callback
# # #             def progress_callback(processed, total):
# # #                 self.job_manager.update_progress(task.job_id, processed, total)
            
# # #             result = self.video_service.moderate(
# # #                 video_path,
# # #                 sampling_fps,
# # #                 progress_callback=progress_callback
# # #             )
            
# # #             self.job_manager.set_result(task.job_id, result.model_dump())
# # #             self.queue_system.mark_completed(TaskType.VIDEO)
            
# # #             if task.callback:
# # #                 task.callback(result)
                
# # #         except Exception as e:
# # #             self.job_manager.set_error(task.job_id, str(e))
# # #             self.queue_system.mark_failed(TaskType.VIDEO)
# # #             raise


# # # class WorkerPool:
# # #     """Pool of workers for each task type"""
    
# # #     def __init__(
# # #         self,
# # #         queue_system: QueueSystem,
# # #         job_manager: JobManager,
# # #         text_service: TextModerationService,
# # #         image_service: ImageModerationService,
# # #         video_service: VideoModerationService,
# # #         num_text_workers: int = 4,
# # #         num_image_workers: int = 8,
# # #         num_video_workers: int = 2
# # #     ):
# # #         self.queue_system = queue_system
# # #         self.job_manager = job_manager
# # #         self.workers: List[BaseWorker] = []
        
# # #         # Create text workers
# # #         for i in range(num_text_workers):
# # #             worker = TextWorker(i, queue_system, job_manager, text_service)
# # #             self.workers.append(worker)
        
# # #         # Create image workers
# # #         for i in range(num_image_workers):
# # #             worker = ImageWorker(i, queue_system, job_manager, image_service)
# # #             self.workers.append(worker)
        
# # #         # Create video workers
# # #         for i in range(num_video_workers):
# # #             worker = VideoWorker(i, queue_system, job_manager, video_service)
# # #             self.workers.append(worker)
    
# # #     def start_all(self):
# # #         """Start all workers"""
# # #         for worker in self.workers:
# # #             worker.start()
# # #         print(f"✅ Started {len(self.workers)} workers")
    
# # #     def stop_all(self):
# # #         """Stop all workers"""
# # #         for worker in self.workers:
# # #             worker.stop()
        
# # #         # Wait for all workers to finish
# # #         for worker in self.workers:
# # #             worker.join(timeout=5.0)
        
# # #         print(f"🔴 Stopped all workers")



# # # app/core/workers.py (Updated VideoWorker with keyframe support)
# # """
# # Worker threads for processing moderation tasks.
# # """
# # import threading
# # import os
# # from typing import List
# # from PIL import Image

# # from src.services.text_moderation import TextModerationService
# # from src.services.image_moderation import ImageModerationService
# # from src.services.video_moderation import VideoModerationService
# # from src.core.queue_system import QueueSystem, Task, TaskType
# # from src.core.job_manager import JobManager, JobStatus


# # class BaseWorker(threading.Thread):
# #     """Base worker thread"""
    
# #     def __init__(
# #         self,
# #         worker_id: int,
# #         queue_system: QueueSystem,
# #         job_manager: JobManager,
# #         task_type: TaskType
# #     ):
# #         super().__init__(daemon=True)
# #         self.worker_id = worker_id
# #         self.queue_system = queue_system
# #         self.job_manager = job_manager
# #         self.task_type = task_type
# #         self.running = False
# #         self.name = f"{task_type.value}-worker-{worker_id}"
    
# #     def run(self):
# #         """Worker main loop"""
# #         self.running = True
# #         print(f"✅ {self.name} started")
        
# #         while self.running:
# #             try:
# #                 task = self.queue_system.get_task(self.task_type, timeout=1.0)
                
# #                 if task:
# #                     self.process_task(task)
# #                     self.queue_system.mark_done(task)
                    
# #             except Exception as e:
# #                 print(f"❌ {self.name} error: {e}")
# #                 if task:
# #                     self.job_manager.set_error(task.job_id, str(e))
# #                     self.queue_system.mark_failed(self.task_type)
        
# #         print(f"🔴 {self.name} stopped")
    
# #     def process_task(self, task: Task):
# #         """Override in subclass"""
# #         raise NotImplementedError
    
# #     def stop(self):
# #         """Stop worker"""
# #         self.running = False


# # class TextWorker(BaseWorker):
# #     """Worker for text moderation"""
    
# #     def __init__(
# #         self,
# #         worker_id: int,
# #         queue_system: QueueSystem,
# #         job_manager: JobManager,
# #         text_service: TextModerationService
# #     ):
# #         super().__init__(worker_id, queue_system, job_manager, TaskType.TEXT)
# #         self.text_service = text_service
    
# #     def process_task(self, task: Task):
# #         """Process text moderation task"""
# #         self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
# #         try:
# #             result = self.text_service.moderate(task.data)
# #             self.job_manager.set_result(task.job_id, result.model_dump())
# #             self.queue_system.mark_completed(TaskType.TEXT)
            
# #             if task.callback:
# #                 task.callback(result)
                
# #         except Exception as e:
# #             self.job_manager.set_error(task.job_id, str(e))
# #             self.queue_system.mark_failed(TaskType.TEXT)
# #             raise


# # class ImageWorker(BaseWorker):
# #     """Worker for image moderation"""
    
# #     def __init__(
# #         self,
# #         worker_id: int,
# #         queue_system: QueueSystem,
# #         job_manager: JobManager,
# #         image_service: ImageModerationService
# #     ):
# #         super().__init__(worker_id, queue_system, job_manager, TaskType.IMAGE)
# #         self.image_service = image_service
    
# #     def process_task(self, task: Task):
# #         """Process image moderation task"""
# #         self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
# #         try:
# #             image: Image.Image = task.data
# #             result = self.image_service.moderate(image)
# #             self.job_manager.set_result(task.job_id, result.model_dump())
# #             self.queue_system.mark_completed(TaskType.IMAGE)
            
# #             if task.callback:
# #                 task.callback(result)
                
# #         except Exception as e:
# #             self.job_manager.set_error(task.job_id, str(e))
# #             self.queue_system.mark_failed(TaskType.IMAGE)
# #             raise


# # class VideoWorker(BaseWorker):
# #     """Worker for video moderation"""
    
# #     def __init__(
# #         self,
# #         worker_id: int,
# #         queue_system: QueueSystem,
# #         job_manager: JobManager,
# #         video_service: VideoModerationService
# #     ):
# #         super().__init__(worker_id, queue_system, job_manager, TaskType.VIDEO)
# #         self.video_service = video_service
    
# #     def process_task(self, task: Task):
# #         """Process video moderation task"""
# #         self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
# #         temp_video_path = None
# #         try:
# #             video_path, sampling_fps, use_keyframes = task.data
# #             temp_video_path = video_path
            
# #             # Progress callback
# #             def progress_callback(processed, total):
# #                 self.job_manager.update_progress(task.job_id, processed, total)
            
# #             result = self.video_service.moderate(
# #                 video_path,
# #                 sampling_fps,
# #                 progress_callback=progress_callback,
# #                 use_keyframes=use_keyframes
# #             )
            
# #             self.job_manager.set_result(task.job_id, result.model_dump())
# #             self.queue_system.mark_completed(TaskType.VIDEO)
            
# #             if task.callback:
# #                 task.callback(result)
                
# #         except Exception as e:
# #             self.job_manager.set_error(task.job_id, str(e))
# #             self.queue_system.mark_failed(TaskType.VIDEO)
# #             raise
# #         finally:
# #             # Clean up temp video file
# #             if temp_video_path and os.path.exists(temp_video_path):
# #                 try:
# #                     os.remove(temp_video_path)
# #                     print(f"   🗑️  Cleaned up temp video: {temp_video_path}")
# #                 except Exception as e:
# #                     print(f"   ⚠️  Failed to clean up temp video: {e}")


# # class WorkerPool:
# #     """Pool of workers for each task type"""
    
# #     def __init__(
# #         self,
# #         queue_system: QueueSystem,
# #         job_manager: JobManager,
# #         text_service: TextModerationService,
# #         image_service: ImageModerationService,
# #         video_service: VideoModerationService,
# #         num_text_workers: int = 4,
# #         num_image_workers: int = 8,
# #         num_video_workers: int = 2
# #     ):
# #         self.queue_system = queue_system
# #         self.job_manager = job_manager
# #         self.workers: List[BaseWorker] = []
        
# #         # Create text workers
# #         for i in range(num_text_workers):
# #             worker = TextWorker(i, queue_system, job_manager, text_service)
# #             self.workers.append(worker)
        
# #         # Create image workers
# #         for i in range(num_image_workers):
# #             worker = ImageWorker(i, queue_system, job_manager, image_service)
# #             self.workers.append(worker)
        
# #         # Create video workers
# #         for i in range(num_video_workers):
# #             worker = VideoWorker(i, queue_system, job_manager, video_service)
# #             self.workers.append(worker)
    
# #     def start_all(self):
# #         """Start all workers"""
# #         for worker in self.workers:
# #             worker.start()
# #         print(f"✅ Started {len(self.workers)} workers")
    
# #     def stop_all(self):
# #         """Stop all workers"""
# #         for worker in self.workers:
# #             worker.stop()
        
# #         for worker in self.workers:
# #             worker.join(timeout=5.0)
        
# #         print(f"🔴 Stopped all workers")



# # app/core/workers.py (Updated with better logging and resource cleanup)
# """
# Worker threads with structured logging and safe resource management.
# """
# import threading
# import os
# import time
# from typing import List
# from PIL import Image

# from src.services.text_moderation import TextModerationService
# from src.services.image_moderation import ImageModerationService
# from src.services.video_moderation import VideoModerationService
# from src.core.queue_system import QueueSystem, Task, TaskType
# from src.core.job_manager import JobManager, JobStatus
# from src.utils.logging_utils import structured_logger
# from src.utils.file_utils import safe_remove_file


# class BaseWorker(threading.Thread):
#     """Base worker thread with structured logging"""
    
#     def __init__(
#         self,
#         worker_id: int,
#         queue_system: QueueSystem,
#         job_manager: JobManager,
#         task_type: TaskType
#     ):
#         super().__init__(daemon=True)
#         self.worker_id = worker_id
#         self.queue_system = queue_system
#         self.job_manager = job_manager
#         self.task_type = task_type
#         self.running = False
#         self.name = f"{task_type.value}-worker-{worker_id}"
#         self.tasks_processed = 0
#         self.tasks_failed = 0
    
#     def run(self):
#         """Worker main loop"""
#         self.running = True
#         structured_logger.info(f"Worker started", worker_name=self.name)
#         print(f"✅ {self.name} started")
        
#         while self.running:
#             task = None
#             try:
#                 task = self.queue_system.get_task(self.task_type, timeout=1.0)
                
#                 if task:
#                     structured_logger.info(
#                         f"Processing task for job {task.job_id[:8]}",
#                         worker_name=self.name
#                     )
                    
#                     start_time = time.time()
#                     self.process_task(task)
#                     elapsed = time.time() - start_time
                    
#                     self.tasks_processed += 1
#                     self.queue_system.mark_done(task)
                    
#                     structured_logger.info(
#                         f"Task completed in {elapsed:.2f}s (total: {self.tasks_processed})",
#                         worker_name=self.name
#                     )
                    
#             except Exception as e:
#                 self.tasks_failed += 1
#                 structured_logger.error(
#                     f"Task failed: {str(e)[:200]} (failures: {self.tasks_failed})",
#                     worker_name=self.name
#                 )
                
#                 if task:
#                     self.job_manager.set_error(task.job_id, str(e))
#                     self.queue_system.mark_failed(self.task_type)
        
#         structured_logger.info(
#             f"Worker stopped (processed: {self.tasks_processed}, failed: {self.tasks_failed})",
#             worker_name=self.name
#         )
#         print(f"🔴 {self.name} stopped")
    
#     def process_task(self, task: Task):
#         """Override in subclass"""
#         raise NotImplementedError
    
#     def stop(self):
#         """Stop worker"""
#         self.running = False
    
#     def get_stats(self) -> dict:
#         """Get worker statistics"""
#         return {
#             "name": self.name,
#             "running": self.running,
#             "tasks_processed": self.tasks_processed,
#             "tasks_failed": self.tasks_failed
#         }


# class TextWorker(BaseWorker):
#     """Worker for text moderation"""
    
#     def __init__(
#         self,
#         worker_id: int,
#         queue_system: QueueSystem,
#         job_manager: JobManager,
#         text_service: TextModerationService
#     ):
#         super().__init__(worker_id, queue_system, job_manager, TaskType.TEXT)
#         self.text_service = text_service
    
#     def process_task(self, task: Task):
#         """Process text moderation task"""
#         self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
#         try:
#             result = self.text_service.moderate(task.data)
#             self.job_manager.set_result(task.job_id, result.model_dump())
#             self.queue_system.mark_completed(TaskType.TEXT)
            
#             if task.callback:
#                 task.callback(result)
                
#         except Exception as e:
#             self.job_manager.set_error(task.job_id, str(e))
#             self.queue_system.mark_failed(TaskType.TEXT)
#             raise


# class ImageWorker(BaseWorker):
#     """Worker for image moderation"""
    
#     def __init__(
#         self,
#         worker_id: int,
#         queue_system: QueueSystem,
#         job_manager: JobManager,
#         image_service: ImageModerationService
#     ):
#         super().__init__(worker_id, queue_system, job_manager, TaskType.IMAGE)
#         self.image_service = image_service
    
#     def process_task(self, task: Task):
#         """Process image moderation task"""
#         self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
#         try:
#             image: Image.Image = task.data
#             result = self.image_service.moderate(image)
#             self.job_manager.set_result(task.job_id, result.model_dump())
#             self.queue_system.mark_completed(TaskType.IMAGE)
            
#             if task.callback:
#                 task.callback(result)
                
#         except Exception as e:
#             self.job_manager.set_error(task.job_id, str(e))
#             self.queue_system.mark_failed(TaskType.IMAGE)
#             raise


# class VideoWorker(BaseWorker):
#     """Worker for video moderation with safe cleanup"""
    
#     def __init__(
#         self,
#         worker_id: int,
#         queue_system: QueueSystem,
#         job_manager: JobManager,
#         video_service: VideoModerationService
#     ):
#         super().__init__(worker_id, queue_system, job_manager, TaskType.VIDEO)
#         self.video_service = video_service
    
#     def process_task(self, task: Task):
#         """Process video moderation task"""
#         self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
#         temp_video_path = None
#         try:
#             video_path, sampling_fps, use_keyframes = task.data
#             temp_video_path = video_path
            
#             # Progress callback
#             def progress_callback(processed, total):
#                 self.job_manager.update_progress(task.job_id, processed, total)
            
#             result = self.video_service.moderate(
#                 video_path,
#                 sampling_fps,
#                 progress_callback=progress_callback,
#                 use_keyframes=use_keyframes,
#                 job_id=task.job_id
#             )
            
#             self.job_manager.set_result(task.job_id, result.model_dump())
#             self.queue_system.mark_completed(TaskType.VIDEO)
            
#             if task.callback:
#                 task.callback(result)
                
#         except Exception as e:
#             self.job_manager.set_error(task.job_id, str(e))
#             self.queue_system.mark_failed(TaskType.VIDEO)
#             raise
#         finally:
#             # Safe cleanup with retry
#             if temp_video_path:
#                 # Small delay to ensure all file handles are released
#                 time.sleep(0.5)
#                 safe_remove_file(temp_video_path, max_retries=5, retry_delay=1.0)


# class WorkerPool:
#     """Pool of workers for each task type"""
    
#     def __init__(
#         self,
#         queue_system: QueueSystem,
#         job_manager: JobManager,
#         text_service: TextModerationService,
#         image_service: ImageModerationService,
#         video_service: VideoModerationService,
#         num_text_workers: int = 4,
#         num_image_workers: int = 8,
#         num_video_workers: int = 2
#     ):
#         self.queue_system = queue_system
#         self.job_manager = job_manager
#         self.workers: List[BaseWorker] = []
        
#         # Create text workers
#         for i in range(num_text_workers):
#             worker = TextWorker(i, queue_system, job_manager, text_service)
#             self.workers.append(worker)
        
#         # Create image workers
#         for i in range(num_image_workers):
#             worker = ImageWorker(i, queue_system, job_manager, image_service)
#             self.workers.append(worker)
        
#         # Create video workers
#         for i in range(num_video_workers):
#             worker = VideoWorker(i, queue_system, job_manager, video_service)
#             self.workers.append(worker)
        
#         structured_logger.info(
#             f"WorkerPool initialized: {num_text_workers} text, "
#             f"{num_image_workers} image, {num_video_workers} video workers"
#         )
    
#     def start_all(self):
#         """Start all workers"""
#         for worker in self.workers:
#             worker.start()
        
#         print(f"\n{'='*70}")
#         print(f"👷 WORKER POOL STARTED")
#         print(f"{'='*70}")
#         print(f"   Text Workers: {sum(1 for w in self.workers if isinstance(w, TextWorker))}")
#         print(f"   Image Workers: {sum(1 for w in self.workers if isinstance(w, ImageWorker))}")
#         print(f"   Video Workers: {sum(1 for w in self.workers if isinstance(w, VideoWorker))}")
#         print(f"   Total: {len(self.workers)} workers")
#         print(f"{'='*70}\n")
        
#         structured_logger.info(f"Started {len(self.workers)} workers")
    
#     def stop_all(self):
#         """Stop all workers"""
#         print("\n🔴 Stopping all workers...")
        
#         for worker in self.workers:
#             worker.stop()
        
#         for worker in self.workers:
#             worker.join(timeout=5.0)
        
#         # Print final stats
#         print(f"\n{'='*70}")
#         print(f"📊 WORKER STATISTICS")
#         print(f"{'='*70}")
        
#         for worker in self.workers:
#             stats = worker.get_stats()
#             print(f"   {stats['name']}: "
#                   f"processed={stats['tasks_processed']}, "
#                   f"failed={stats['tasks_failed']}")
        
#         print(f"{'='*70}\n")
        
#         structured_logger.info("All workers stopped")
    
#     def get_stats(self) -> dict:
#         """Get pool statistics"""
#         return {
#             "workers": [w.get_stats() for w in self.workers],
#             "total_workers": len(self.workers),
#             "active_workers": sum(1 for w in self.workers if w.running)
#         }




# app/core/workers.py (Fixed VideoWorker)
"""
Worker threads with structured logging and safe resource management.
"""
import threading
import os
import time
from typing import List
from PIL import Image

from src.schemas.models import KeyframeMethod
from src.services.text_moderation import TextModerationService
from src.services.image_moderation import ImageModerationService
from src.services.video_moderation import VideoModerationService
from src.core.queue_system import QueueSystem, Task, TaskType
from src.core.job_manager import JobManager, JobStatus
from src.utils.logging_utils import structured_logger
from src.utils.file_utils import safe_remove_file


class BaseWorker(threading.Thread):
    """Base worker thread with structured logging"""
    
    def __init__(
        self,
        worker_id: int,
        queue_system: QueueSystem,
        job_manager: JobManager,
        task_type: TaskType
    ):
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.queue_system = queue_system
        self.job_manager = job_manager
        self.task_type = task_type
        self.running = False
        self.name = f"{task_type.value}-worker-{worker_id}"
        self.tasks_processed = 0
        self.tasks_failed = 0
    
    def run(self):
        """Worker main loop"""
        self.running = True
        structured_logger.info(f"Worker started", worker_name=self.name)
        print(f"✅ {self.name} started")
        
        while self.running:
            task = None
            try:
                task = self.queue_system.get_task(self.task_type, timeout=1.0)
                
                if task:
                    structured_logger.info(
                        f"Processing task for job {task.job_id[:8]}",
                        worker_name=self.name
                    )
                    
                    start_time = time.time()
                    self.process_task(task)
                    elapsed = time.time() - start_time
                    
                    self.tasks_processed += 1
                    self.queue_system.mark_done(task)
                    
                    structured_logger.info(
                        f"Task completed in {elapsed:.2f}s (total: {self.tasks_processed})",
                        worker_name=self.name
                    )
                    
            except Exception as e:
                self.tasks_failed += 1
                structured_logger.error(
                    f"Task failed: {str(e)[:200]} (failures: {self.tasks_failed})",
                    worker_name=self.name
                )
                print(f"❌ {self.name} error: {e}")
                
                if task:
                    self.job_manager.set_error(task.job_id, str(e))
                    self.queue_system.mark_failed(self.task_type)
        
        structured_logger.info(
            f"Worker stopped (processed: {self.tasks_processed}, failed: {self.tasks_failed})",
            worker_name=self.name
        )
        print(f"🔴 {self.name} stopped")
    
    def process_task(self, task: Task):
        """Override in subclass"""
        raise NotImplementedError
    
    def stop(self):
        """Stop worker"""
        self.running = False
    
    def get_stats(self) -> dict:
        """Get worker statistics"""
        return {
            "name": self.name,
            "running": self.running,
            "tasks_processed": self.tasks_processed,
            "tasks_failed": self.tasks_failed
        }


class TextWorker(BaseWorker):
    """Worker for text moderation"""
    
    def __init__(
        self,
        worker_id: int,
        queue_system: QueueSystem,
        job_manager: JobManager,
        text_service: TextModerationService
    ):
        super().__init__(worker_id, queue_system, job_manager, TaskType.TEXT)
        self.text_service = text_service
    
    def process_task(self, task: Task):
        """Process text moderation task"""
        self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
        try:
            result = self.text_service.moderate(task.data)
            self.job_manager.set_result(task.job_id, result.model_dump())
            self.queue_system.mark_completed(TaskType.TEXT)
            
            if task.callback:
                task.callback(result)
                
        except Exception as e:
            self.job_manager.set_error(task.job_id, str(e))
            self.queue_system.mark_failed(TaskType.TEXT)
            raise


class ImageWorker(BaseWorker):
    """Worker for image moderation"""
    
    def __init__(
        self,
        worker_id: int,
        queue_system: QueueSystem,
        job_manager: JobManager,
        image_service: ImageModerationService
    ):
        super().__init__(worker_id, queue_system, job_manager, TaskType.IMAGE)
        self.image_service = image_service
    
    def process_task(self, task: Task):
        """Process image moderation task"""
        self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
        try:
            image: Image.Image = task.data
            result = self.image_service.moderate(image)
            self.job_manager.set_result(task.job_id, result.model_dump())
            self.queue_system.mark_completed(TaskType.IMAGE)
            
            if task.callback:
                task.callback(result)
                
        except Exception as e:
            self.job_manager.set_error(task.job_id, str(e))
            self.queue_system.mark_failed(TaskType.IMAGE)
            raise


class VideoWorker(BaseWorker):
    """Worker for video moderation with safe cleanup"""
    
    def __init__(
        self,
        worker_id: int,
        queue_system: QueueSystem,
        job_manager: JobManager,
        video_service: VideoModerationService
    ):
        super().__init__(worker_id, queue_system, job_manager, TaskType.VIDEO)
        self.video_service = video_service
    
    def process_task(self, task: Task):
        """Process video moderation task"""
        self.job_manager.update_status(task.job_id, JobStatus.PROCESSING)
        
        temp_video_path = None
        try:
            # Unpack task data (6 parameters)
            (
                video_path,
                sampling_fps,
                keyframe_method,
                scene_detector_type,
                scene_threshold,
                min_scene_length
            ) = task.data
            
            temp_video_path = video_path
            
            structured_logger.info(
                f"Video task params: method={keyframe_method.value}, "
                f"sampling_fps={sampling_fps}, "
                f"scene_detector={scene_detector_type}, "
                f"scene_threshold={scene_threshold}",
                worker_name=self.name
            )
            
            # Progress callback
            def progress_callback(processed, total):
                self.job_manager.update_progress(task.job_id, processed, total)
            
            # Call moderate with all parameters
            result = self.video_service.moderate(
                video_path=video_path,
                sampling_fps=sampling_fps,
                progress_callback=progress_callback,
                keyframe_method=keyframe_method,
                job_id=task.job_id,
                scene_detector_type=scene_detector_type,
                scene_threshold=scene_threshold,
                min_scene_length=min_scene_length
            )
            
            self.job_manager.set_result(task.job_id, result.model_dump())
            self.queue_system.mark_completed(TaskType.VIDEO)
            
            if task.callback:
                task.callback(result)
                
        except Exception as e:
            structured_logger.error(
                f"Video moderation error: {str(e)}",
                worker_name=self.name
            )
            self.job_manager.set_error(task.job_id, str(e))
            self.queue_system.mark_failed(TaskType.VIDEO)
            raise
        finally:
            # Safe cleanup with retry
            if temp_video_path:
                # Small delay to ensure all file handles are released
                time.sleep(0.5)
                safe_remove_file(temp_video_path, max_retries=5, retry_delay=1.0)


class WorkerPool:
    """Pool of workers for each task type"""
    
    def __init__(
        self,
        queue_system: QueueSystem,
        job_manager: JobManager,
        text_service: TextModerationService,
        image_service: ImageModerationService,
        video_service: VideoModerationService,
        num_text_workers: int = 4,
        num_image_workers: int = 8,
        num_video_workers: int = 2
    ):
        self.queue_system = queue_system
        self.job_manager = job_manager
        self.workers: List[BaseWorker] = []
        
        # Create text workers
        for i in range(num_text_workers):
            worker = TextWorker(i, queue_system, job_manager, text_service)
            self.workers.append(worker)
        
        # Create image workers
        for i in range(num_image_workers):
            worker = ImageWorker(i, queue_system, job_manager, image_service)
            self.workers.append(worker)
        
        # Create video workers
        for i in range(num_video_workers):
            worker = VideoWorker(i, queue_system, job_manager, video_service)
            self.workers.append(worker)
        
        structured_logger.info(
            f"WorkerPool initialized: {num_text_workers} text, "
            f"{num_image_workers} image, {num_video_workers} video workers"
        )
    
    def start_all(self):
        """Start all workers"""
        for worker in self.workers:
            worker.start()
        
        print(f"\n{'='*70}")
        print(f"👷 WORKER POOL STARTED")
        print(f"{'='*70}")
        print(f"   Text Workers: {sum(1 for w in self.workers if isinstance(w, TextWorker))}")
        print(f"   Image Workers: {sum(1 for w in self.workers if isinstance(w, ImageWorker))}")
        print(f"   Video Workers: {sum(1 for w in self.workers if isinstance(w, VideoWorker))}")
        print(f"   Total: {len(self.workers)} workers")
        print(f"{'='*70}\n")
        
        structured_logger.info(f"Started {len(self.workers)} workers")
    
    def stop_all(self):
        """Stop all workers"""
        print("\n🔴 Stopping all workers...")
        
        for worker in self.workers:
            worker.stop()
        
        for worker in self.workers:
            worker.join(timeout=5.0)
        
        # Print final stats
        print(f"\n{'='*70}")
        print(f"📊 WORKER STATISTICS")
        print(f"{'='*70}")
        
        for worker in self.workers:
            stats = worker.get_stats()
            print(f"   {stats['name']}: "
                  f"processed={stats['tasks_processed']}, "
                  f"failed={stats['tasks_failed']}")
        
        print(f"{'='*70}\n")
        
        structured_logger.info("All workers stopped")
    
    def get_stats(self) -> dict:
        """Get pool statistics"""
        return {
            "workers": [w.get_stats() for w in self.workers],
            "total_workers": len(self.workers),
            "active_workers": sum(1 for w in self.workers if w.running)
        }