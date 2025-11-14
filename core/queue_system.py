# app/core/queue_system.py
"""
Queue system for distributing moderation tasks to workers.
"""
import queue
import threading
from typing import Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum


class TaskType(str, Enum):
    """Task type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    VIDEO_BATCH = "video_batch"
    KEYFRAME = "keyframe"


@dataclass
class Task:
    """Task data structure"""
    job_id: str
    task_type: TaskType
    data: Any
    callback: Callable = None
    priority: int = 1  # Lower number = higher priority


class PriorityQueue:
    """Priority queue wrapper with task type separation"""
    
    def __init__(self, maxsize: int = 0):
        self.queue = queue.PriorityQueue(maxsize=maxsize)
        self._counter = 0
        self._lock = threading.Lock()
    
    def put(self, task: Task, block: bool = True, timeout: float = None):
        """Put task into queue with priority"""
        with self._lock:
            # Use counter to maintain FIFO order for same priority
            self.queue.put((task.priority, self._counter, task), block, timeout)
            self._counter += 1
    
    def get(self, block: bool = True, timeout: float = None) -> Task:
        """Get task from queue"""
        _, _, task = self.queue.get(block, timeout)
        return task
    
    def task_done(self):
        """Mark task as done"""
        self.queue.task_done()
    
    def qsize(self) -> int:
        """Get queue size"""
        return self.queue.qsize()
    
    def empty(self) -> bool:
        """Check if queue is empty"""
        return self.queue.empty()


class QueueSystem:
    """
    Multi-queue system for different task types.
    """
    
    def __init__(
        self,
        text_queue_size: int = 1000,
        image_queue_size: int = 5000,
        video_queue_size: int = 100
    ):
        """
        Initialize queue system.
        
        Args:
            text_queue_size: Max size of text queue
            image_queue_size: Max size of image queue
            video_queue_size: Max size of video queue
        """
        self.queues: Dict[TaskType, PriorityQueue] = {
            TaskType.TEXT: PriorityQueue(maxsize=text_queue_size),
            TaskType.IMAGE: PriorityQueue(maxsize=image_queue_size),
            TaskType.VIDEO: PriorityQueue(maxsize=video_queue_size),
            TaskType.VIDEO_BATCH: PriorityQueue(maxsize=video_queue_size),
            TaskType.KEYFRAME: PriorityQueue(maxsize=video_queue_size)
        }
        self.stats = {
            task_type: {"submitted": 0, "completed": 0, "failed": 0}
            for task_type in TaskType
        }
        self._stats_lock = threading.Lock()
    
    def submit_task(self, task: Task, timeout: float = 5.0) -> bool:
        """
        Submit task to appropriate queue.
        
        Args:
            task: Task to submit
            timeout: Queue put timeout
            
        Returns:
            bool: True if submitted successfully
        """
        try:
            self.queues[task.task_type].put(task, timeout=timeout)
            
            with self._stats_lock:
                self.stats[task.task_type]["submitted"] += 1
            
            return True
        except queue.Full:
            print(f"⚠️  Queue full for {task.task_type}")
            return False
    
    def get_task(self, task_type: TaskType, timeout: float = 1.0) -> Task:
        """
        Get task from queue.
        
        Args:
            task_type: Type of task to get
            timeout: Queue get timeout
            
        Returns:
            Task or None if timeout
        """
        try:
            return self.queues[task_type].get(timeout=timeout)
        except queue.Empty:
            return None
    
    def mark_done(self, task: Task):
        """Mark task as done"""
        self.queues[task.task_type].task_done()
    
    def mark_completed(self, task_type: TaskType):
        """Update completion stats"""
        with self._stats_lock:
            self.stats[task_type]["completed"] += 1
    
    def mark_failed(self, task_type: TaskType):
        """Update failure stats"""
        with self._stats_lock:
            self.stats[task_type]["failed"] += 1
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        with self._stats_lock:
            return {
                task_type.value: {
                    **stats,
                    "queue_size": self.queues[task_type].qsize()
                }
                for task_type, stats in self.stats.items()
            }


# Global queue system instance
queue_system = QueueSystem()