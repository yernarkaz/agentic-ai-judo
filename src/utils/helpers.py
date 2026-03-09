import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """
    Load configuration from .env file.

    Returns:
        Dictionary with configuration values
    """
    load_dotenv()
    return {
        "max_frames": int(os.getenv("FRAME_EXTRACTION_MAX_FRAMES", "50")),
        "scene_change_threshold": float(os.getenv("SCENE_CHANGE_THRESHOLD", "30")),
        "motion_threshold": float(os.getenv("MOTION_THRESHOLD", "15")),
        "gpt_model": os.getenv("GPT_MODEL", "gpt-4o"),
        "output_dir": os.getenv("OUTPUT_DIR", "output"),
    }


def setup_directories(base_path: str) -> dict:
    """
    Create necessary directories for storing intermediate and final results.

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
    if not os.path.exists(data_dir):
        return []
    return [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.lower().endswith(video_extensions)
    ]


def format_timestamp(seconds: float) -> str:
    """Convert seconds to mm:ss timestamp string."""
    minutes = int(seconds) // 60
    remaining_seconds = int(seconds) % 60
    return f"{minutes:02d}:{remaining_seconds:02d}"
