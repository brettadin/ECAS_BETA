"""Unit tests for analysis job lifecycle, fault isolation, and checkpoint resumption."""
import pytest

from ecas.analysis.jobs import (
    AnalysisJob,
    AnalysisJobRunner,
    CancellationToken,
    JobCancelledError,
    JobStatus,
    get_software_environment,
    validate_checkpoint_resumability,
)


class TestAnalysisJobs:
    def test_job_serialization(self):
        job = AnalysisJob(
            job_id="test_job_1",
            name="WASP-39b Forward Model Sweep",
            job_type="forward_model_sweep",
            target_id="WASP-39 b",
            input_hashes={"obs.csv": "a" * 64},
            config={"temperature_k": 1166.0},
        )
        data = job.to_dict()
        assert data["job_id"] == "test_job_1"
        assert data["status"] == "Queued"

        reloaded = AnalysisJob.from_dict(data)
        assert reloaded.job_id == job.job_id
        assert reloaded.config["temperature_k"] == 1166.0

    def test_job_runner_batch_success_and_fault_isolation(self):
        job = AnalysisJob(
            job_id="batch_job_1",
            name="Batch Test",
            job_type="batch_test",
            target_id="WASP-39 b",
        )
        runner = AnalysisJobRunner(job)

        items = ["item_ok_1", "item_bad_2", "item_ok_3"]

        def process_fn(item, cancel_token):
            if "bad" in item:
                raise ValueError("Simulated item corruption")
            return f"Processed {item}"

        results = runner.run_batch(items, process_fn)
        assert job.status == JobStatus.COMPLETED
        assert len(results["completed"]) == 2
        assert "0" in results["completed"]  # item_ok_1
        assert "2" in results["completed"]  # item_ok_3
        assert len(results["failures"]) == 1
        assert "Simulated item corruption" in results["failures"]["1"]

    def test_job_runner_cooperative_cancellation(self):
        job = AnalysisJob(
            job_id="cancel_job_1",
            name="Cancel Test",
            job_type="batch_test",
            target_id="WASP-39 b",
        )
        runner = AnalysisJobRunner(job)

        items = ["item_1", "item_2", "item_3"]

        def process_fn(item, cancel_token):
            if item == "item_2":
                runner.cancel()
            return f"Processed {item}"

        results = runner.run_batch(items, process_fn)
        assert job.status == JobStatus.CANCELLED
        assert results.get("cancelled") is True
        assert len(results["completed"]) >= 1

    def test_checkpoint_resumption_validation(self):
        job = AnalysisJob(
            job_id="resumable_job",
            name="Resumable",
            job_type="batch_test",
            target_id="WASP-39 b",
            status=JobStatus.CANCELLED,
            can_resume=True,
            checkpoint_data={"completed_items": {"item_1": "result"}},
            input_hashes={"obs.csv": "a" * 64},
            config={"temperature_k": 1166.0},
        )

        # 1. Matching hashes and config -> valid resumption
        valid, msg = validate_checkpoint_resumability(
            job,
            current_input_hashes={"obs.csv": "a" * 64},
            current_config={"temperature_k": 1166.0},
        )
        assert valid
        assert "Checkpoint verified" in msg

        # 2. Changed raw-byte hash -> rejected
        valid_bad_hash, msg_hash = validate_checkpoint_resumability(
            job,
            current_input_hashes={"obs.csv": "b" * 64},
            current_config={"temperature_k": 1166.0},
        )
        assert not valid_bad_hash
        assert "SHA-256 hash has changed" in msg_hash

        # 3. Changed model parameter -> rejected
        valid_bad_cfg, msg_cfg = validate_checkpoint_resumability(
            job,
            current_input_hashes={"obs.csv": "a" * 64},
            current_config={"temperature_k": 1400.0},
        )
        assert not valid_bad_cfg
        assert "Configuration setting 'temperature_k' changed" in msg_cfg

