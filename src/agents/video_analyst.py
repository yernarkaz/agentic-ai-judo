"""Video Analysis Agent that extracts frames and performs video analysis."""

import os
import cv2
import base64
from typing import List, Dict, Any, Optional

from .base import BaseAgent


class VideoAnalysisAgent(BaseAgent):
    """Agent responsible for analyzing video files."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Video Analysis Agent.

        Args:
            config: Configuration dictionary with options:
                - frame_interval: Extract frame every N seconds
                - quality_threshold: Minimum quality score
        """
        super().__init__("VideoAnalysisAgent", config)
        self.frame_interval = self.config.get("frame_interval", 30)
        self.quality_threshold = self.config.get("quality_threshold", 0.7)

    def load_video(self, video_path: str) -> Dict[str, Any]:
        """
        Load a video file and extract metadata.

        Args:
            video_path: Path to the video file

        Returns:
            Dictionary with video metadata
        """
        if not os.path.exists(video_path):
            return {"error": f"Video file not found: {video_path}"}

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return {"error": f"Could not open video: {video_path}"}

        metadata = {
            "path": video_path,
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration_seconds": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            / cap.get(cv2.CAP_PROP_FPS),
        }

        cap.release()
        return metadata

    def extract_frames(self, video_path: str) -> List[Dict[str, Any]]:
        """
        Extract frames from a video at specified intervals.

        Args:
            video_path: Path to the video file

        Returns:
            List of frame data dictionaries
        """
        if not os.path.exists(video_path):
            return [{"error": f"Video file not found: {video_path}"}]

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return [{"error": f"Could not open video: {video_path}"}]

        fps = cap.get(cv2.CAP_PROP_FPS)
        interval_frames = int(fps * self.frame_interval)
        frames = []
        frame_num = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_num % interval_frames == 0:
                # Convert frame to base64 for processing
                _, buffer = cv2.imencode(".jpg", frame)
                import base64

                frame_data = {
                    "frame_number": frame_num,
                    "timestamp": frame_num / fps,
                    "width": frame.shape[1],
                    "height": frame.shape[0],
                    "frame": base64.b64encode(buffer).decode("utf-8"),
                }
                frames.append(frame_data)

            frame_num += 1

        cap.release()
        return frames

    def assess_video_quality(self, video_path: str) -> Dict[str, Any]:
        """
        Assess the quality of a video.

        Args:
            video_path: Path to the video file

        Returns:
            Dictionary with quality metrics
        """
        metadata = self.load_video(video_path)

        if "error" in metadata:
            return metadata

        quality = {
            "path": video_path,
            "resolution": f"{metadata['width']}x{metadata['height']}",
            "fps": round(metadata["fps"], 2),
            "duration": f"{metadata['duration_seconds']:.2f}s",
            "total_frames": metadata["frame_count"],
            "quality_score": self._calculate_quality_score(metadata),
        }

        return quality

    def _calculate_quality_score(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate a quality score based on video properties.

        Args:
            metadata: Video metadata dictionary

        Returns:
            Quality score between 0 and 1
        """
        # Score based on resolution
        resolution = metadata["width"] * metadata["height"]
        resolution_score = min(1.0, resolution / (1920 * 1080))

        # Score based on FPS
        fps = metadata["fps"]
        fps_score = min(1.0, fps / 30)

        # Score based on duration (longer videos are generally better)
        duration = metadata["duration_seconds"]
        duration_score = min(1.0, duration / 300)  # Max score for 5 min videos

        # Weighted average
        score = (resolution_score * 0.5) + (fps_score * 0.3) + (duration_score * 0.2)
        return round(score, 2)

    def detect_scene_changes(
        self, video_path: str, threshold: float = 0.1
    ) -> List[int]:
        """
        Detect scene changes in a video.

        Args:
            video_path: Path to the video file
            threshold: Difference threshold for scene change detection

        Returns:
            List of frame numbers where scene changes occur
        """
        if not os.path.exists(video_path):
            return [{"error": f"Video file not found: {video_path}"}]

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return [{"error": f"Could not open video: {video_path}"}]

        scene_changes = []
        prev_frame = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert to grayscale for comparison
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_frame is not None:
                # Calculate absolute difference
                diff = cv2.absdiff(prev_frame, gray)
                non_zero = cv2.countNonZero(diff)

                # Normalize and check threshold
                height, width = gray.shape
                diff_ratio = non_zero / (height * width)

                if diff_ratio > threshold:
                    scene_changes.append(cap.get(cv2.CAP_PROP_POS_FRAMES))

            prev_frame = gray

        cap.release()
        return scene_changes

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process video input.

        Accepts input with:
            - video_path: Path to the video file
            - action: What action to perform (extract_frames, assess_quality, detect_scenes)

        Args:
            input_data: Dictionary with video path and action

        Returns:
            Dictionary with processing results
        """
        video_path = input_data.get("video_path")
        action = input_data.get("action", "extract_frames")

        if not video_path:
            return {"error": "No video_path provided"}

        if action == "extract_frames":
            return {"frames": self.extract_frames(video_path)}
        elif action == "assess_quality":
            return self.assess_video_quality(video_path)
        elif action == "detect_scenes":
            return {"scene_changes": self.detect_scene_changes(video_path)}
        else:
            return {"error": f"Unknown action: {action}"}

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
