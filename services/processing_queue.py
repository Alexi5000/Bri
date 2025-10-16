"""
Processing Queue Manager for BRI
Handles multiple video processing jobs with priority queue
"""

import asyncio
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from utils.logging_config import get_logger

logger = get_logger(__name__)


class JobPriority(Enum):
    """Job priority levels."""
    HIGH = 1  # User-requested processing
    NORMAL = 2  # Background processing
    LOW = 3  # Reprocessing/optimization


@dataclass(order=True)
class ProcessingJob:
    """Represents a video processing job."""
    priority: int = field(compare=True)
    video_id: str = field(compare=False)
    video_path: str = field(compare=False)
    created_at: float = field(default_factory=time.time, compare=False)
    started_at: Optional[float] = field(default=None, compare=False)
    completed_at: Optional[float] = field(default=None, compare=False)
    status: str = field(default='queued', compare=False)  # queued, processing, complete, failed
    error: Optional[str] = field(default=None, compare=False)


class ProcessingQueue:
    """
    Manages video processing jobs with priority queue.
    
    Features:
    - Priority-based job scheduling (user-requested > background)
    - Concurrent processing (configurable max workers)
    - Graceful shutdown (finish current jobs)
    - Job status tracking
    """
    
    def __init__(self, max_concurrent_jobs: int = 2):
        """
        Initialize Processing Queue.
        
        Args:
            max_concurrent_jobs: Maximum number of concurrent processing jobs
        """
        self.max_concurrent_jobs = max_concurrent_jobs
        
        # Job queue (priority queue using sorted list)
        self.queue: List[ProcessingJob] = []
        
        # Active jobs (currently processing)
        self.active_jobs: Dict[str, ProcessingJob] = {}
        
        # Completed jobs history (keep last 100)
        self.completed_jobs: deque = deque(maxlen=100)
        
        # Worker tasks
        self.workers: List[asyncio.Task] = []
        
        # Shutdown flag
        self.shutdown_requested = False
        
        # Lock for thread-safe operations
        self.lock = asyncio.Lock()
        
        logger.info(f"Processing Queue initialized (max_concurrent={max_concurrent_jobs})")
    
    async def add_job(
        self,
        video_id: str,
        video_path: str,
        priority: JobPriority = JobPriority.NORMAL
    ) -> ProcessingJob:
        """
        Add a job to the processing queue.
        
        Args:
            video_id: Video identifier
            video_path: Path to video file
            priority: Job priority level
            
        Returns:
            ProcessingJob instance
        """
        async with self.lock:
            # Check if job already exists
            if video_id in self.active_jobs:
                logger.info(f"Job for video {video_id} already processing")
                return self.active_jobs[video_id]
            
            # Check if job is in queue
            for job in self.queue:
                if job.video_id == video_id:
                    logger.info(f"Job for video {video_id} already queued")
                    return job
            
            # Create new job
            job = ProcessingJob(
                priority=priority.value,
                video_id=video_id,
                video_path=video_path
            )
            
            # Add to queue (maintain sorted order by priority)
            self.queue.append(job)
            self.queue.sort()
            
            logger.info(
                f"Added job for video {video_id} with priority {priority.name} "
                f"(queue size: {len(self.queue)})"
            )
            
            return job
    
    async def get_next_job(self) -> Optional[ProcessingJob]:
        """
        Get next job from queue (highest priority).
        
        Returns:
            ProcessingJob or None if queue is empty
        """
        async with self.lock:
            if not self.queue:
                return None
            
            # Get highest priority job (first in sorted list)
            job = self.queue.pop(0)
            
            # Mark as processing
            job.status = 'processing'
            job.started_at = time.time()
            
            # Add to active jobs
            self.active_jobs[job.video_id] = job
            
            logger.info(
                f"Starting job for video {job.video_id} "
                f"(active: {len(self.active_jobs)}, queued: {len(self.queue)})"
            )
            
            return job
    
    async def complete_job(
        self,
        video_id: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Mark a job as complete.
        
        Args:
            video_id: Video identifier
            success: Whether job completed successfully
            error: Error message if failed
        """
        async with self.lock:
            job = self.active_jobs.get(video_id)
            if not job:
                logger.warning(f"Job for video {video_id} not found in active jobs")
                return
            
            # Update job status
            job.completed_at = time.time()
            job.status = 'complete' if success else 'failed'
            job.error = error
            
            # Move to completed jobs
            self.completed_jobs.append(job)
            del self.active_jobs[video_id]
            
            duration = job.completed_at - job.started_at if job.started_at else 0
            logger.info(
                f"Completed job for video {video_id} "
                f"(status: {job.status}, duration: {duration:.1f}s)"
            )
    
    async def start_workers(self) -> None:
        """
        Start worker tasks to process jobs from queue.
        """
        logger.info(f"Starting {self.max_concurrent_jobs} worker tasks")
        
        for i in range(self.max_concurrent_jobs):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
    
    async def _worker(self, worker_id: int) -> None:
        """
        Worker task that processes jobs from queue.
        
        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")
        
        while not self.shutdown_requested:
            try:
                # Get next job
                job = await self.get_next_job()
                
                if job is None:
                    # No jobs available, wait a bit
                    await asyncio.sleep(1.0)
                    continue
                
                # Process job
                logger.info(f"Worker {worker_id} processing video {job.video_id}")
                
                try:
                    await self._process_job(job)
                    await self.complete_job(job.video_id, success=True)
                    
                except Exception as e:
                    logger.error(f"Worker {worker_id} job failed: {e}")
                    await self.complete_job(
                        job.video_id,
                        success=False,
                        error=str(e)
                    )
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _process_job(self, job: ProcessingJob) -> None:
        """
        Process a video job using progressive processor.
        
        Args:
            job: ProcessingJob to execute
        """
        from services.progressive_processor import get_progressive_processor
        
        processor = get_progressive_processor()
        
        await processor.process_video_progressive(
            job.video_id,
            job.video_path
        )
    
    async def shutdown(self, timeout: float = 30.0) -> None:
        """
        Gracefully shutdown queue (finish current jobs).
        
        Args:
            timeout: Maximum time to wait for jobs to complete (seconds)
        """
        logger.info("Shutdown requested, finishing current jobs...")
        
        self.shutdown_requested = True
        
        # Wait for workers to finish (with timeout)
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.workers, return_exceptions=True),
                timeout=timeout
            )
            logger.info("All workers stopped gracefully")
        except asyncio.TimeoutError:
            logger.warning(f"Shutdown timeout after {timeout}s, cancelling workers")
            for worker in self.workers:
                worker.cancel()
        
        # Log final stats
        logger.info(
            f"Queue shutdown complete: "
            f"active={len(self.active_jobs)}, "
            f"queued={len(self.queue)}, "
            f"completed={len(self.completed_jobs)}"
        )
    
    def get_status(self) -> Dict:
        """
        Get current queue status.
        
        Returns:
            Dictionary with queue statistics
        """
        return {
            'active_jobs': len(self.active_jobs),
            'queued_jobs': len(self.queue),
            'completed_jobs': len(self.completed_jobs),
            'workers': len(self.workers),
            'shutdown_requested': self.shutdown_requested
        }
    
    def get_job_status(self, video_id: str) -> Optional[Dict]:
        """
        Get status of a specific job.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Job status dictionary or None if not found
        """
        # Check active jobs
        if video_id in self.active_jobs:
            job = self.active_jobs[video_id]
            return {
                'video_id': job.video_id,
                'status': job.status,
                'priority': job.priority,
                'started_at': job.started_at,
                'duration': time.time() - job.started_at if job.started_at else 0
            }
        
        # Check queue
        for job in self.queue:
            if job.video_id == video_id:
                return {
                    'video_id': job.video_id,
                    'status': job.status,
                    'priority': job.priority,
                    'position': self.queue.index(job) + 1,
                    'queue_size': len(self.queue)
                }
        
        # Check completed jobs
        for job in self.completed_jobs:
            if job.video_id == video_id:
                duration = job.completed_at - job.started_at if job.started_at and job.completed_at else 0
                return {
                    'video_id': job.video_id,
                    'status': job.status,
                    'priority': job.priority,
                    'duration': duration,
                    'error': job.error
                }
        
        return None


# Global queue instance
_queue_instance: Optional[ProcessingQueue] = None


def get_processing_queue() -> ProcessingQueue:
    """
    Get or create global processing queue instance.
    
    Returns:
        ProcessingQueue instance
    """
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = ProcessingQueue(max_concurrent_jobs=2)
    return _queue_instance


async def start_queue_workers():
    """Start processing queue workers."""
    queue = get_processing_queue()
    await queue.start_workers()


async def shutdown_queue():
    """Shutdown processing queue gracefully."""
    queue = get_processing_queue()
    await queue.shutdown()
