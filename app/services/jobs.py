"""
In-memory job storage for async analysis tasks.
Simple dict-based storage - works for single instance deployments.
"""
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


# In-memory storage
_jobs: Dict[str, Dict[str, Any]] = {}

# Job TTL - cleanup jobs older than this
JOB_TTL_HOURS = 2


def create_job(url: str) -> str:
    """Create a new job, return job_id."""
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "id": job_id,
        "url": url,
        "status": JobStatus.PENDING,
        "result": None,
        "error": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    logger.info(f"Created job {job_id} for {url}")
    return job_id


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job by ID."""
    return _jobs.get(job_id)


def update_job(job_id: str, status: JobStatus, result: Any = None, error: str = None):
    """Update job status and result."""
    if job_id not in _jobs:
        logger.warning(f"Job {job_id} not found for update")
        return

    _jobs[job_id]["status"] = status
    _jobs[job_id]["updated_at"] = datetime.utcnow()

    if result is not None:
        _jobs[job_id]["result"] = result
    if error is not None:
        _jobs[job_id]["error"] = error

    logger.info(f"Updated job {job_id} to {status}")


def cleanup_old_jobs():
    """Remove jobs older than TTL."""
    cutoff = datetime.utcnow() - timedelta(hours=JOB_TTL_HOURS)
    to_delete = [
        job_id for job_id, job in _jobs.items()
        if job["created_at"] < cutoff
    ]
    for job_id in to_delete:
        del _jobs[job_id]

    if to_delete:
        logger.info(f"Cleaned up {len(to_delete)} old jobs")


def get_job_count() -> int:
    """Get current job count (for monitoring)."""
    return len(_jobs)
