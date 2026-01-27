import os
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from src.video_processing.frame_extractor import FrameExtractor
from src.frame_captioning.caption_generator import FrameCaptioner
from src.llm_analysis.judo_analyzer import JudoAnalyzer
from src.utils.helpers import setup_directories, get_video_files

# Load environment variables
load_dotenv()

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
        self.paths = setup_directories(workspace_dir)

        # Initialize components
        self.frame_extractor = FrameExtractor(fps=1)
        self.captioner = FrameCaptioner()
        self.analyzer = JudoAnalyzer()

    def process_video(self, video_path: str) -> str:
        """
        Process a single video through the entire pipeline.

        Args:
            video_path: Path to the video file

        Returns:
            Path to the analysis output file
        """
        try:
            # Create output directory for this video
            video_name = Path(video_path).stem
            video_output_dir = os.path.join(self.paths["frames"], video_name)

            # Extract frames
            logger.info(f"Extracting frames from {video_path}")
            frame_paths = self.frame_extractor.extract_frames(
                video_path, video_output_dir
            )

            # Generate captions
            logger.info("Generating captions for frames")
            captions = self.captioner.process_frames(frame_paths)

            # Analyze sequence
            logger.info("Analyzing judo sequence")
            analysis = self.analyzer.analyze_sequence(captions)

            # Save analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_path = os.path.join(
                self.paths["analysis"], f"{video_name}_{timestamp}.txt"
            )

            with open(analysis_path, "w") as f:
                f.write(analysis)

            logger.info(f"Analysis saved to {analysis_path}")
            return analysis_path

        except Exception as e:
            logger.error(f"Error processing video {video_path}: {str(e)}")
            raise

    def process_all_videos(self, data_dir: str) -> list:
        """
        Process all videos in the data directory.

        Args:
            data_dir: Directory containing video files

        Returns:
            List of paths to analysis output files
        """
        video_files = get_video_files(data_dir)
        analysis_files = []

        for video_file in video_files:
            try:
                analysis_path = self.process_video(video_file)
                analysis_files.append(analysis_path)
            except Exception as e:
                logger.error(f"Skipping {video_file} due to error: {str(e)}")
                continue

        return analysis_files


def main():
    # Get the project root directory
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(workspace_dir, "data")

    # Initialize and run pipeline
    pipeline = JudoAnalysisPipeline(workspace_dir)
    analysis_files = pipeline.process_all_videos(data_dir)

    logger.info(f"Processing complete. Generated {len(analysis_files)} analysis files.")


if __name__ == "__main__":
    main()
