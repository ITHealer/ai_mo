# app/services/batch_processor.py
"""
Batch processor for image moderation.
"""
import threading
import time
from typing import List, Dict
from queue import Queue
from PIL import Image

from src.services.image_moderation import ImageModerationService
from src.core.job_manager import JobManager, JobStatus
from src.schemas.models import ImageModerationResponse


class ImageBatchProcessor:
    """
    Batch processor for efficient image moderation.
    """
    
    def __init__(
        self,
        image_service: ImageModerationService,
        job_manager: JobManager,
        batch_size: int = 8,
        batch_timeout: float = 2.0
    ):
        """
        Initialize batch processor.
        
        Args:
            image_service: Image moderation service
            job_manager: Job manager
            batch_size: Number of images to batch together
            batch_timeout: Max time to wait for batch to fill (seconds)
        """
        self.image_service = image_service
        self.job_manager = job_manager
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        
        self.batch_queue = Queue()
        self.running = False
        self.processor_thread = None
    
    def start(self):
        """Start batch processor thread"""
        if not self.running:
            self.running = True
            self.processor_thread = threading.Thread(
                target=self._process_batches,
                daemon=True
            )
            self.processor_thread.start()
            print(f"✅ ImageBatchProcessor started (batch_size={self.batch_size})")
    
    def stop(self):
        """Stop batch processor"""
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5.0)
        print("🔴 ImageBatchProcessor stopped")
    
    def submit(self, job_id: str, image: Image.Image):
        """Submit image for batch processing"""
        self.batch_queue.put((job_id, image))
    
    def _process_batches(self):
        """Main batch processing loop"""
        while self.running:
            batch = []
            batch_start = time.time()
            
            # Collect batch
            while len(batch) < self.batch_size:
                timeout = self.batch_timeout - (time.time() - batch_start)
                if timeout <= 0:
                    break
                
                try:
                    item = self.batch_queue.get(timeout=min(timeout, 0.5))
                    batch.append(item)
                except:
                    break
            
            # Process batch if not empty
            if batch:
                self._process_batch(batch)
    
    def _process_batch(self, batch: List[tuple]):
        """
        Process a batch of images.
        
        Args:
            batch: List of (job_id, image) tuples
        """
        print(f"📦 Processing batch of {len(batch)} images")
        
        # Process in parallel using threading
        threads = []
        
        for job_id, image in batch:
            thread = threading.Thread(
                target=self._process_single,
                args=(job_id, image)
            )
            thread.start()
            threads.append(thread)
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
    
    def _process_single(self, job_id: str, image: Image.Image):
        """Process single image"""
        try:
            self.job_manager.update_status(job_id, JobStatus.PROCESSING)
            result = self.image_service.moderate(image)
            self.job_manager.set_result(job_id, result.model_dump())
        except Exception as e:
            self.job_manager.set_error(job_id, str(e))