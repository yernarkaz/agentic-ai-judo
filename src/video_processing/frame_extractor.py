import cv2
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrameExtractor:
    def __init__(self, fps=1):
        """Initialize frame extractor with given frames per second rate."""
        self.fps = fps

    def extract_frames(self, video_path: str, output_dir: str) -> list:
        """
        Extract frames from a video file at specified FPS.

        Args:
            video_path: Path to the video file
            output_dir: Directory to save extracted frames

        Returns:
            List of paths to extracted frames
        """
        try:
            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Open video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Error opening video file: {video_path}")

            # Get video properties
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(video_fps / self.fps)

            frame_paths = []
            frame_count = 0
            success = True

            while success:
                success, frame = cap.read()
                if not success:
                    break

                if frame_count % frame_interval == 0:
                    frame_path = os.path.join(
                        output_dir, f"frame_{frame_count:04d}.jpg"
                    )
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)

                frame_count += 1

            logger.info(f"Extracted {len(frame_paths)} frames from {video_path}")
            return frame_paths

        except Exception as e:
            logger.error(f"Error processing video {video_path}: {str(e)}")
            raise

        finally:
            if "cap" in locals():
                cap.release()
