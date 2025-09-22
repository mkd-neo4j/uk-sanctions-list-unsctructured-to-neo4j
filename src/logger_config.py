"""
Professional logging configuration for the UK Sanctions Pipeline.
Designed for bank demonstrations with clear visibility and progress tracking.
"""

import logging
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and professional styling for console output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        # Get the color for this log level
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']

        # Create timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')

        # Format the message with color
        if record.levelname == 'INFO':
            # For INFO messages, use clean formatting
            formatted = f"{log_color}[{timestamp}] {record.getMessage()}{reset_color}"
        else:
            # For other levels, include the level name
            formatted = f"{log_color}[{timestamp}] {record.levelname}: {record.getMessage()}{reset_color}"

        return formatted


class PipelineLogger:
    """Professional logger for the sanctions pipeline with progress tracking."""

    def __init__(self, name: str = "UKSanctionsPipeline"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_console_handler()

        self.start_time = datetime.now()
        self.step_start_time = None

    def _setup_console_handler(self):
        """Setup console handler with custom formatting."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        formatter = ColoredFormatter()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

    def pipeline_start(self, title: str):
        """Log the start of the pipeline."""
        self.logger.info("=" * 60)
        self.logger.info(f"🏦 {title}")
        self.logger.info("=" * 60)
        self.start_time = datetime.now()

    def step_start(self, step_name: str, description: str = ""):
        """Log the start of a pipeline step."""
        self.step_start_time = datetime.now()
        self.logger.info("")
        self.logger.info(f"📋 STEP: {step_name}")
        if description:
            self.logger.info(f"   {description}")
        self.logger.info("-" * 40)

    def step_complete(self, step_name: str, details: Optional[dict] = None):
        """Log the completion of a pipeline step."""
        if self.step_start_time:
            elapsed = datetime.now() - self.step_start_time
            self.logger.info(f"✅ {step_name} completed in {elapsed.total_seconds():.1f}s")
        else:
            self.logger.info(f"✅ {step_name} completed")

        if details:
            for key, value in details.items():
                self.logger.info(f"   • {key}: {value}")

    def step_error(self, step_name: str, error: str):
        """Log a step error."""
        if self.step_start_time:
            elapsed = datetime.now() - self.step_start_time
            self.logger.error(f"❌ {step_name} failed after {elapsed.total_seconds():.1f}s")
        else:
            self.logger.error(f"❌ {step_name} failed")
        self.logger.error(f"   Error: {error}")

    def progress(self, current: int, total: int, item_name: str, details: str = ""):
        """Log progress for operations with multiple items."""
        percentage = (current / total) * 100
        progress_bar = self._create_progress_bar(percentage)

        if details:
            self.logger.info(f"⚡ {progress_bar} {current}/{total} {item_name} - {details}")
        else:
            self.logger.info(f"⚡ {progress_bar} {current}/{total} {item_name}")

    def data_sample(self, title: str, data: dict):
        """Log a sample of extracted data."""
        self.logger.info(f"📊 {title}:")
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 100:
                display_value = value[:100] + "..."
            else:
                display_value = value
            self.logger.info(f"   • {key}: {display_value}")

    def metrics(self, title: str, metrics: dict):
        """Log performance metrics."""
        self.logger.info(f"📈 {title}:")
        for metric, value in metrics.items():
            self.logger.info(f"   • {metric}: {value}")

    def pipeline_complete(self):
        """Log the completion of the entire pipeline."""
        total_time = datetime.now() - self.start_time
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info(f"🎯 Pipeline completed successfully in {total_time.total_seconds():.1f}s")
        self.logger.info("=" * 60)

    def info(self, message: str):
        """Log an info message."""
        self.logger.info(message)

    def warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)

    def error(self, message: str):
        """Log an error message."""
        self.logger.error(message)

    def _create_progress_bar(self, percentage: float, width: int = 20) -> str:
        """Create a visual progress bar."""
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:5.1f}%"


# Global logger instance
pipeline_logger = PipelineLogger()