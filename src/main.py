"""
Judo Analysis Pipeline — Main orchestrator.

Processes judo match videos through:
  1. Smart frame extraction (scene detection + motion scoring)
  2. GPT-4o Vision multi-pass analysis
  3. Structured output with text and JSON reports
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from src.video_processing.frame_extractor import FrameExtractor
from src.llm_analysis.judo_analyzer import JudoAnalyzer
from src.utils.helpers import setup_directories, get_video_files, load_config

# Load environment variables
load_dotenv("config/.env")
load_dotenv(override=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JudoAnalysisPipeline:
    def __init__(self, workspace_dir: str):
        """
        Initialize the Judo analysis pipeline.

        Args:
            workspace_dir: Base directory for the project
        """
        self.workspace_dir = workspace_dir
        self.config = load_config()
        self.paths = setup_directories(workspace_dir)

        # Initialize components with config
        self.frame_extractor = FrameExtractor(
            max_frames=self.config.get("max_frames", 50),
            scene_change_threshold=self.config.get("scene_change_threshold", 30.0),
            motion_threshold=self.config.get("motion_threshold", 15.0),
        )
        self.analyzer = JudoAnalyzer(
            model=self.config.get("gpt_model", "gpt-4o"),
        )

    def process_video(self, video_path: str) -> str:
        """
        Process a single video through the entire pipeline.

        Args:
            video_path: Path to the video file

        Returns:
            Path to the analysis output directory
        """
        try:
            video_name = Path(video_path).stem
            video_output_dir = os.path.join(self.paths["frames"], video_name)

            # Step 1: Extract key frames
            logger.info(f"Step 1/2: Extracting key frames from {Path(video_path).name}")
            frame_infos = self.frame_extractor.extract_frames(
                video_path, video_output_dir
            )

            if not frame_infos:
                raise ValueError("No frames were extracted from the video")

            # Compute video duration from last frame timestamp
            duration_sec = max(f.timestamp_sec for f in frame_infos)

            # Step 2: Run GPT-4o Vision analysis
            logger.info("Step 2/2: Running GPT-4o Vision analysis...")
            analysis = self.analyzer.analyze_match(
                frames=frame_infos,
                video_filename=Path(video_path).name,
                duration_sec=duration_sec,
            )

            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_dir = os.path.join(self.paths["analysis"], video_name)
            Path(analysis_dir).mkdir(parents=True, exist_ok=True)

            # Save JSON report
            json_path = os.path.join(analysis_dir, f"analysis_{timestamp}.json")
            with open(json_path, "w") as f:
                json.dump(analysis.to_dict(), f, indent=2)

            # Save human-readable text report
            text_path = os.path.join(analysis_dir, f"report_{timestamp}.txt")
            with open(text_path, "w") as f:
                f.write(analysis.to_text_report())

            logger.info(f"Analysis saved:")
            logger.info(f"  JSON: {json_path}")
            logger.info(f"  Report: {text_path}")

            return analysis_dir

        except Exception as e:
            logger.error(f"Error processing video {video_path}: {str(e)}")
            raise

    def process_all_videos(self, data_dir: str) -> list:
        """
        Process all videos in the data directory.

        Args:
            data_dir: Directory containing video files

        Returns:
            List of paths to analysis output directories
        """
        video_files = get_video_files(data_dir)
        logger.info(f"Found {len(video_files)} video(s) to process")

        analysis_dirs = []

        for video_file in video_files:
            try:
                analysis_dir = self.process_video(video_file)
                analysis_dirs.append(analysis_dir)
            except Exception as e:
                logger.error(f"Skipping {video_file} due to error: {str(e)}")
                continue

        return analysis_dirs


def main():
    """Run the pipeline on all videos in the data directory."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")

    pipeline = JudoAnalysisPipeline(project_root)
    analysis_dirs = pipeline.process_all_videos(data_dir)

    logger.info(
        f"Processing complete. Generated {len(analysis_dirs)} analysis report(s)."
    )


if __name__ == "__main__":
    main()
