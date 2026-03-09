import cv2
import os
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FrameInfo:
    """Metadata about an extracted frame."""
    path: str
    timestamp_sec: float
    frame_number: int
    motion_score: float
    is_scene_change: bool


class FrameExtractor:
    def __init__(
        self,
        max_frames: int = 50,
        scene_change_threshold: float = 30.0,
        motion_threshold: float = 15.0,
        min_interval_sec: float = 0.5,
    ):
        """
        Initialize smart frame extractor for judo video analysis.

        Args:
            max_frames: Maximum number of key frames to extract
            scene_change_threshold: Threshold for scene change detection (0-255)
            motion_threshold: Minimum motion score to consider a frame "action"
            min_interval_sec: Minimum seconds between extracted frames
        """
        self.max_frames = max_frames
        self.scene_change_threshold = scene_change_threshold
        self.motion_threshold = motion_threshold
        self.min_interval_sec = min_interval_sec

    def _compute_motion_score(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """Compute motion intensity between two consecutive frames."""
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(prev_gray, curr_gray)
        return float(np.mean(diff))

    def _is_scene_change(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> bool:
        """Detect if there's a significant scene change between frames."""
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

        # Use histogram comparison for more robust scene detection
        hist_prev = cv2.calcHist([prev_gray], [0], None, [256], [0, 256])
        hist_curr = cv2.calcHist([curr_gray], [0], None, [256], [0, 256])
        cv2.normalize(hist_prev, hist_prev)
        cv2.normalize(hist_curr, hist_curr)

        correlation = cv2.compareHist(hist_prev, hist_curr, cv2.HISTCMP_CORREL)
        # Low correlation means big scene change
        return correlation < (1.0 - self.scene_change_threshold / 100.0)

    def _sample_uniformly(self, total_frames: int, fps: float) -> List[int]:
        """Get a set of uniformly spaced frame indices as a baseline."""
        # Sample roughly every 2 seconds as baseline candidates
        interval = int(fps * 2)
        return list(range(0, total_frames, max(interval, 1)))

    def extract_frames(self, video_path: str, output_dir: str) -> List[FrameInfo]:
        """
        Extract key frames from a video using smart selection.

        Strategy:
        1. Scan the entire video computing motion scores at regular intervals
        2. Identify scene changes and high-motion moments
        3. Select the top frames by motion score, respecting min_interval
        4. Always include first and last frames for context

        Args:
            video_path: Path to the video file
            output_dir: Directory to save extracted frames

        Returns:
            List of FrameInfo objects for extracted frames
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_frames / video_fps if video_fps > 0 else 0

        logger.info(
            f"Video: {Path(video_path).name} | "
            f"{total_frames} frames | "
            f"{video_fps:.1f} FPS | "
            f"{duration_sec:.1f}s duration"
        )

        # Phase 1: Scan video and compute motion scores at candidate positions
        candidate_indices = self._sample_uniformly(total_frames, video_fps)
        candidates = []  # (frame_index, motion_score, is_scene_change)

        prev_frame = None
        for idx in candidate_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue

            if prev_frame is not None:
                motion = self._compute_motion_score(prev_frame, frame)
                scene_change = self._is_scene_change(prev_frame, frame)
                candidates.append((idx, motion, scene_change, frame))
            else:
                # Always include first frame
                candidates.append((idx, 0.0, False, frame))

            prev_frame = frame

        logger.info(f"Scanned {len(candidates)} candidate positions")

        # Phase 2: Score and rank candidates
        # Prioritize: scene changes > high motion > uniform coverage
        scored = []
        for idx, motion, scene_change, frame in candidates:
            score = motion
            if scene_change:
                score += 50.0  # Boost scene changes
            if motion > self.motion_threshold:
                score += 20.0  # Boost action frames
            scored.append((idx, score, motion, scene_change, frame))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Phase 3: Select top frames respecting minimum interval
        min_interval_frames = int(self.min_interval_sec * video_fps)
        selected = []
        selected_indices = set()

        for idx, score, motion, scene_change, frame in scored:
            if len(selected) >= self.max_frames:
                break

            # Check minimum interval from already selected frames
            too_close = any(
                abs(idx - sel_idx) < min_interval_frames
                for sel_idx in selected_indices
            )
            if too_close:
                continue

            selected.append((idx, motion, scene_change, frame))
            selected_indices.add(idx)

        # Sort selected frames by timestamp for sequential output
        selected.sort(key=lambda x: x[0])

        # Phase 4: Save frames and build metadata
        frame_infos = []
        for i, (idx, motion, scene_change, frame) in enumerate(selected):
            timestamp_sec = idx / video_fps if video_fps > 0 else 0
            frame_path = os.path.join(output_dir, f"frame_{i:03d}_{idx:06d}.jpg")

            # Resize for API efficiency (max 1024px on longest side)
            h, w = frame.shape[:2]
            max_dim = 1024
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

            info = FrameInfo(
                path=frame_path,
                timestamp_sec=round(timestamp_sec, 2),
                frame_number=idx,
                motion_score=round(motion, 2),
                is_scene_change=scene_change,
            )
            frame_infos.append(info)

        cap.release()

        logger.info(
            f"Extracted {len(frame_infos)} key frames "
            f"(scene changes: {sum(1 for f in frame_infos if f.is_scene_change)}, "
            f"high motion: {sum(1 for f in frame_infos if f.motion_score > self.motion_threshold)})"
        )

        return frame_infos
