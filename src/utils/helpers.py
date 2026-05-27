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
    Checks both project root .env and config/.env as fallback.

    Returns:
        Dictionary with configuration values
    """
    load_dotenv("config/.env")  # load real config first
    load_dotenv(override=False)  # root .env only fills gaps
    return {
        "max_frames": int(os.getenv("FRAME_EXTRACTION_MAX_FRAMES", "50")),
        "scene_change_threshold": float(os.getenv("SCENE_CHANGE_THRESHOLD", "30")),
        "motion_threshold": float(os.getenv("MOTION_THRESHOLD", "15")),
        "ollama_model": os.getenv("OLLAMA_MODEL", "qwen2.5vl:7b"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
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
    """Get all video files from the data directory (recursive)."""
    video_extensions = (".mp4", ".mov", ".avi")
    if not os.path.exists(data_dir):
        return []
    result = []
    for root, _dirs, files in os.walk(data_dir):
        for f in files:
            if f.lower().endswith(video_extensions):
                result.append(os.path.join(root, f))
    return sorted(result)


def format_timestamp(seconds: float) -> str:
    """Convert seconds to mm:ss timestamp string."""
    minutes = int(seconds) // 60
    remaining_seconds = int(seconds) % 60
    return f"{minutes:02d}:{remaining_seconds:02d}"
