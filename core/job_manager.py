# app/core/job_manager.py
"""
Job management system for async content moderation.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
import threading


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobProgress:
    """Job progress tracking"""
    total: int = 0
    processed: int = 0
    
    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.processed / self.total) * 100, 2)


@dataclass
class Job:
    """Job data structure"""
    job_id: str
    job_type: str  # text, image, video, video_batch
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: JobProgress = field(default_factory=JobProgress)
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class JobManager:
    """
    Thread-safe job manager for tracking moderation jobs.
    """
    
    def __init__(self, max_jobs_in_memory: int = 10000):
        """
        Initialize job manager.
        
        Args:
            max_jobs_in_memory: Maximum number of jobs to keep in memory
        """
        self.jobs: Dict[str, Job] = {}
        self.max_jobs = max_jobs_in_memory
        self._lock = threading.Lock()
    
    def create_job(self, job_type: str, metadata: Dict[str, Any] = None) -> str:
        """
        Create a new job.
        
        Args:
            job_type: Type of job (text, image, video, video_batch)
            metadata: Optional metadata
            
        Returns:
            job_id: UUID of created job
        """
        job_id = str(uuid.uuid4())
        
        with self._lock:
            # Clean up old jobs if limit reached
            if len(self.jobs) >= self.max_jobs:
                self._cleanup_oldest_jobs()
            
            job = Job(
                job_id=job_id,
                job_type=job_type,
                status=JobStatus.PENDING,
                created_at=datetime.now(),
                metadata=metadata or {}
            )
            self.jobs[job_id] = job
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        with self._lock:
            return self.jobs.get(job_id)
    
    def update_status(self, job_id: str, status: JobStatus):
        """Update job status"""
        with self._lock:
            if job := self.jobs.get(job_id):
                job.status = status
                
                if status == JobStatus.PROCESSING and not job.started_at:
                    job.started_at = datetime.now()
                elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    job.completed_at = datetime.now()
    
    def update_progress(self, job_id: str, processed: int, total: int = None):
        """Update job progress"""
        with self._lock:
            if job := self.jobs.get(job_id):
                job.progress.processed = processed
                if total is not None:
                    job.progress.total = total
    
    def set_result(self, job_id: str, result: Any):
        """Set job result"""
        with self._lock:
            if job := self.jobs.get(job_id):
                job.result = result
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
    
    def set_error(self, job_id: str, error: str):
        """Set job error"""
        with self._lock:
            if job := self.jobs.get(job_id):
                job.error = error
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
    
    def _cleanup_oldest_jobs(self, keep_recent: int = 5000):
        """Clean up oldest completed/failed jobs"""
        completed_jobs = [
            (job_id, job) for job_id, job in self.jobs.items()
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
        ]
        
        if len(completed_jobs) > keep_recent:
            # Sort by completion time and remove oldest
            completed_jobs.sort(key=lambda x: x[1].completed_at or datetime.min)
            to_remove = len(completed_jobs) - keep_recent
            
            for job_id, _ in completed_jobs[:to_remove]:
                del self.jobs[job_id]


# Global job manager instance
job_manager = JobManager()