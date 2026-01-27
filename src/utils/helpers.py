import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_directories(base_path: str) -> dict:
    """
    Create necessary directories for storing intermediate results.

    Returns:
        Dictionary containing paths to different directories
    """
    paths = {
        "frames": os.path.join(base_path, "output", "frames"),
        "analysis": os.path.join(base_path, "output", "analysis"),
    }

    for path in paths.values():
        Path(path).mkdir(parents=True, exist_ok=True)

    return paths


def get_video_files(data_dir: str) -> list:
    """Get all video files from the data directory."""
    video_extensions = (".mp4", ".mov", ".avi")
    return [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.lower().endswith(video_extensions)
    ]


def format_timestamp(frame_number: int, fps: float = 1.0) -> str:
    """Convert frame number to timestamp string."""
    seconds = int(frame_number / fps)
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:02d}"
