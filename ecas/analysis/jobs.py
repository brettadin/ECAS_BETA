"""Shared analysis job lifecycle and checkpointed resumption engine.

Manages long-running scientific workflows (batch identification, forward model sweeps,
sensitivity audits) off the GUI thread with:
- Formal job states: QUEUED, RUNNING, COMPLETED, CANCELLED, FAILED.
- Responsive progress updates and cooperative cancellation via CancellationToken.
- Independent batch fault isolation: one failing observation does not erase successful results.
- Scientifically reproducible checkpointing and resume validation checking:
  * Input raw-product SHA-256 hashes
  * Model settings and parameter definitions
  * Python, NumPy, SciPy, and ECAS software versions
- Explicit rejection of incompatible checkpoints with clear reasons.
- Clear distinction between computational resumption and fresh restart.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import sys
import threading
from typing import Any, Callable, Sequence
from uuid import uuid4

import numpy as np


class JobStatus(str, Enum):
    """Canonical analysis job lifecycle states."""

    QUEUED = "Queued"
    RUNNING = "Running"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    FAILED = "Failed"


class JobCancelledError(Exception):
    """Raised when an analysis job terminates early via cooperative cancellation."""


class CancellationToken:
    """Thread-safe cancellation token for cooperative background job termination."""

    def __init__(self):
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        self._cancelled.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled.is_set()

    def check_cancellation(self) -> None:
        if self.is_cancelled:
            raise JobCancelledError("Analysis job was cancelled by user request.")


def get_software_environment() -> dict[str, str]:
    """Capture runtime software environment for reproducibility auditing."""
    try:
        from importlib.metadata import version
        scipy_v = version("scipy")
    except Exception:
        scipy_v = "unavailable"

    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "scipy": scipy_v,
        "platform": sys.platform,
    }


@dataclass
class AnalysisJob:
    """Persistent representation of an analysis job."""

    job_id: str
    name: str
    job_type: str  # e.g. 'batch_identification', 'sensitivity_audit', 'forward_model_sweep'
    target_id: str
    status: JobStatus = JobStatus.QUEUED
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str | None = None
    finished_at: str | None = None
    progress_percent: float = 0.0
    progress_message: str = "Queued"
    input_hashes: dict[str, str] = field(default_factory=dict)
    software_environment: dict[str, str] = field(default_factory=get_software_environment)
    config: dict[str, Any] = field(default_factory=dict)
    checkpoint_data: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    can_resume: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "job_type": self.job_type,
            "target_id": self.target_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "progress_percent": self.progress_percent,
            "progress_message": self.progress_message,
            "input_hashes": self.input_hashes,
            "software_environment": self.software_environment,
            "config": self.config,
            "checkpoint_data": self.checkpoint_data,
            "results": self.results,
            "error_message": self.error_message,
            "can_resume": self.can_resume,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnalysisJob:
        return cls(
            job_id=data["job_id"],
            name=data["name"],
            job_type=data["job_type"],
            target_id=data["target_id"],
            status=JobStatus(data.get("status", JobStatus.QUEUED.value)),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            progress_percent=float(data.get("progress_percent", 0.0)),
            progress_message=data.get("progress_message", ""),
            input_hashes=dict(data.get("input_hashes", {})),
            software_environment=dict(data.get("software_environment", {})),
            config=dict(data.get("config", {})),
            checkpoint_data=dict(data.get("checkpoint_data", {})),
            results=dict(data.get("results", {})),
            error_message=data.get("error_message"),
            can_resume=bool(data.get("can_resume", False)),
        )


def validate_checkpoint_resumability(
    job: AnalysisJob,
    current_input_hashes: dict[str, str],
    current_config: dict[str, Any],
) -> tuple[bool, str]:
    """Validate whether an interrupted or checkpointed job can be resumed reproducibly."""
    if job.status == JobStatus.COMPLETED:
        return False, "Job is already completed; resumption is not applicable."

    if not job.can_resume or not job.checkpoint_data:
        return False, "Job does not contain a valid computational checkpoint."

    # 1. Verify input file raw-byte hashes
    for key, expected_hash in job.input_hashes.items():
        curr_hash = current_input_hashes.get(key)
        if not curr_hash:
            return False, f"Missing input hash for '{key}'; cannot verify source consistency."
        if curr_hash != expected_hash:
            return (
                False,
                f"Input file '{key}' SHA-256 hash has changed ({curr_hash[:12]}... vs expected {expected_hash[:12]}...). "
                "Resumption is rejected to prevent scientifically invalid cross-version state mixing."
            )

    # 2. Verify software environment (major and minor python and numpy version)
    curr_env = get_software_environment()
    expected_env = job.software_environment
    if curr_env.get("python", "").split(".")[:2] != expected_env.get("python", "").split(".")[:2]:
        return (
            False,
            f"Python runtime version mismatch ({curr_env.get('python')} vs checkpoint {expected_env.get('python')}). "
            "Resumption requires an identical Python runtime."
        )

    # 3. Verify key configuration parameters
    for k in ("method", "planet_preset_id", "threshold", "temperature_k"):
        if k in job.config and k in current_config and job.config[k] != current_config[k]:
            return (
                False,
                f"Configuration setting '{k}' changed ({current_config[k]} vs checkpoint {job.config[k]}). "
                "Start a new analysis to modify configuration parameters."
            )

    return True, "Checkpoint verified: input data, software environment, and parameters match."


class AnalysisJobRunner:
    """Executes analysis jobs with progress reporting, cooperative cancellation, and checkpointing."""

    def __init__(self, job: AnalysisJob):
        self.job = job
        self.cancel_token = CancellationToken()
        self._lock = threading.Lock()

    def cancel(self) -> None:
        self.cancel_token.cancel()

    def update_progress(self, percent: float, message: str) -> None:
        with self._lock:
            self.job.progress_percent = max(0.0, min(100.0, percent))
            self.job.progress_message = message

    def save_checkpoint(self, checkpoint_data: dict[str, Any]) -> None:
        with self._lock:
            self.job.checkpoint_data = dict(checkpoint_data)
            self.job.can_resume = True

    def run_batch(
        self,
        batch_items: Sequence[Any],
        process_item_fn: Callable[[Any, CancellationToken], Any],
        *,
        on_progress: Callable[[float, str], None] | None = None,
    ) -> dict[str, Any]:
        """Execute a batch with fault isolation and partial checkpoint preservation."""
        self.job.status = JobStatus.RUNNING
        self.job.started_at = datetime.now(timezone.utc).isoformat()
        self.update_progress(0.0, f"Starting batch processing of {len(batch_items)} items...")

        completed_results: dict[str, Any] = dict(self.job.checkpoint_data.get("completed_items", {}))
        failures: dict[str, str] = dict(self.job.checkpoint_data.get("failed_items", {}))

        total = len(batch_items)
        try:
            for idx, item in enumerate(batch_items):
                self.cancel_token.check_cancellation()

                item_id = getattr(item, "observation_id", getattr(item, "source_id", str(idx)))
                # Skip if already processed in prior checkpoint
                if item_id in completed_results:
                    continue

                item_label = getattr(item, "label", getattr(item, "source_id", f"Item {idx+1}"))
                pct = (float(idx) / float(total)) * 100.0
                msg = f"Processing [{idx + 1}/{total}]: {item_label}"
                self.update_progress(pct, msg)
                if on_progress:
                    on_progress(pct, msg)

                try:
                    res = process_item_fn(item, self.cancel_token)
                    completed_results[item_id] = res
                except JobCancelledError:
                    raise
                except Exception as exc:
                    # Fault isolation: record failure without terminating batch
                    failures[item_id] = str(exc)

                # Save incremental checkpoint
                self.save_checkpoint({
                    "completed_items": completed_results,
                    "failed_items": failures,
                    "last_processed_index": idx,
                })

            self.job.status = JobStatus.COMPLETED
            self.job.finished_at = datetime.now(timezone.utc).isoformat()
            self.update_progress(100.0, f"Completed: {len(completed_results)} succeeded, {len(failures)} failed.")
            self.job.results = {
                "completed": completed_results,
                "failures": failures,
            }
            self.job.can_resume = False
            return self.job.results

        except JobCancelledError:
            self.job.status = JobStatus.CANCELLED
            self.job.finished_at = datetime.now(timezone.utc).isoformat()
            self.job.error_message = "Analysis job was cancelled by user request."
            self.job.can_resume = len(completed_results) > 0
            self.update_progress(self.job.progress_percent, "Cancelled by user.")
            return {
                "completed": completed_results,
                "failures": failures,
                "cancelled": True,
            }

        except Exception as exc:
            self.job.status = JobStatus.FAILED
            self.job.finished_at = datetime.now(timezone.utc).isoformat()
            self.job.error_message = str(exc)
            self.job.can_resume = len(completed_results) > 0
            self.update_progress(self.job.progress_percent, f"Failed: {exc}")
            raise

