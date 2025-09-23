"""
Progress tracking and metrics utilities for extraction processing.
Handles performance monitoring, timing, and progress reporting.
"""

import time
from typing import List, Dict, Any
from src.logger_config import pipeline_logger


class ProgressTracker:
    """Tracks processing progress and performance metrics."""

    def __init__(self):
        """Initialize progress tracker with empty metrics."""
        self.processing_times: List[float] = []
        self.extraction_errors = 0
        self.start_time = None

    def start_processing(self) -> None:
        """Mark the start of processing."""
        self.start_time = time.time()

    def track_record_processing(self, record_start_time: float) -> float:
        """
        Track the processing time for a single record.

        Args:
            record_start_time: Time when record processing started

        Returns:
            Processing time for this record in seconds
        """
        record_time = time.time() - record_start_time
        self.processing_times.append(record_time)
        return record_time

    def increment_errors(self) -> None:
        """Increment the error counter."""
        self.extraction_errors += 1

    def report_progress(self, current: int, total: int, item_type: str, message: str) -> None:
        """
        Report processing progress for current item.

        Args:
            current: Current item number
            total: Total number of items
            item_type: Type of items being processed (e.g., "individuals", "entities")
            message: Additional message to display
        """
        pipeline_logger.progress(current, total, item_type, message)

    def show_example_output(self, record_number: int, raw_text: str, structured_data: Dict[str, Any],
                          processing_time: float, is_individual: bool = True) -> None:
        """
        Show detailed example output for first few records.

        Args:
            record_number: Which record this is (1-based)
            raw_text: The original raw input text
            structured_data: The extracted structured data
            processing_time: How long this record took to process
            is_individual: True for individuals, False for entities
        """
        if record_number == 1:
            item_type = "INDIVIDUAL" if is_individual else "ENTITY"
            emoji = "🔍" if is_individual else "🔍"

            pipeline_logger.info("")
            pipeline_logger.info(f"{emoji} {item_type} EXAMPLE: Raw Input vs Structured Output")
            pipeline_logger.info("=" * 60)
            pipeline_logger.info("📄 RAW INPUT TEXT:")

            # Show first 300 characters of raw input
            raw_preview = raw_text[:300] + "..." if len(raw_text) > 300 else raw_text
            pipeline_logger.info(f"   {raw_preview}")

            pipeline_logger.info("")
            pipeline_logger.info("🤖 AI STRUCTURED OUTPUT:")

            for key, value in structured_data.items():
                pipeline_logger.info(f"   • {key}: {value}")

            pipeline_logger.info(f"   • Processing time: {processing_time:.2f}s")
            pipeline_logger.info("=" * 60)

        elif record_number <= 3:
            # Show brief data for other early records
            sample_data = {**structured_data, "Processing time": f"{processing_time:.2f}s"}
            item_type = "Individual" if is_individual else "Entity"
            pipeline_logger.data_sample(f"{item_type} {record_number} Extracted", sample_data)

    def calculate_final_metrics(self, total_records: int, successful_extractions: int) -> Dict[str, Any]:
        """
        Calculate final processing metrics.

        Args:
            total_records: Total number of records processed
            successful_extractions: Number of successful extractions

        Returns:
            Dictionary containing processing metrics
        """
        total_time = time.time() - self.start_time if self.start_time else 0
        avg_time_per_record = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0

        return {
            "Records processed": f"{total_records}",
            "Successful extractions": f"{successful_extractions}",
            "Failed extractions": f"{self.extraction_errors}",
            "Success rate": f"{(successful_extractions/total_records*100):.1f}%" if total_records > 0 else "0%",
            "Total processing time": f"{total_time:.1f}s",
            "Average time per record": f"{avg_time_per_record:.2f}s"
        }

    def report_metrics(self, metrics_title: str, metrics: Dict[str, Any]) -> None:
        """
        Report metrics using the pipeline logger.

        Args:
            metrics_title: Title for the metrics report
            metrics: Dictionary of metrics to report
        """
        pipeline_logger.metrics(metrics_title, metrics)