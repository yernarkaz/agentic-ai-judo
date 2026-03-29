"""Pose Analysis Agent that detects and tracks judo players using MediaPipe."""

import cv2
import mediapipe as mp
from typing import List, Dict, Any, Optional
import base64
import numpy as np

from .base import BaseAgent


class PoseAnalysisAgent(BaseAgent):
    """Agent responsible for pose estimation and tracking."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Pose Analysis Agent.

        Args:
            config: Configuration dictionary with options:
                - confidence_threshold: Minimum confidence for pose detection
        """
        super().__init__("PoseAnalysisAgent", config)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.5)

        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=self.confidence_threshold,
            min_tracking_confidence=self.confidence_threshold,
        )

    def detect_poses_in_frame(
        self, frame_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect poses in a frame.

        Args:
            frame_data: Dictionary containing frame data with 'frame' key (base64)

        Returns:
            List of pose detection results
        """
        # Decode base64 image
        image_data = base64.b64decode(frame_data["frame"])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame
        results = self.pose.process(rgb_frame)

        poses = []

        if results.pose_landmarks:
            pose_landmarks = []
            for i, landmark in enumerate(results.pose_landmarks.landmark):
                pose_landmarks.append({
                    "landmark_id": i,
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z,
                    "visibility": landmark.visibility,
                })

            # Calculate body angles
            angles = self._calculate_angles(results.pose_landmarks)

            # Get bounding box
            bbox = self._calculate_bbox(results.pose_landmarks, frame.shape)

            poses.append({
                "frame_number": frame_data.get("frame_number", 0),
                "timestamp": frame_data.get("timestamp", 0),
                "num_landmarks": len(pose_landmarks),
                "landmarks": pose_landmarks,
                "angles": angles,
                "bbox": bbox,
                "confidence": self._calculate_confidence(results.pose_landmarks),
            })

        return poses

    def _calculate_angles(self, landmarks) -> Dict[str, float]:
        """
        Calculate key body angles from pose landmarks.

        Args:
            landmarks: MediaPipe pose landmarks

        Returns:
            Dictionary of angle names and values
        """
        angles = {}

        # Helper to get angle between three points
        def get_angle(a, b, c):
            a = np.array([a.x, a.y])
            b = np.array([b.x, b.y])
            c = np.array([c.x, c.y])

            ba = a - b
            bc = c - b

            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
            angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
            return np.degrees(angle)

        # Define key angles (landmark indices from MediaPipe)
        # 11: left shoulder, 12: right shoulder
        # 13: left elbow, 14: right elbow
        # 15: left wrist, 16: right wrist
        # 23: left hip, 24: right hip
        # 25: left knee, 26: right knee
        # 27: left ankle, 28: right ankle

        landmark_list = list(landmarks.landmark)

        # Calculate key angles
        try:
            # Elbow angles
            angles["left_elbow"] = get_angle(
                landmark_list[13], landmark_list[11], landmark_list[15]
            )
            angles["right_elbow"] = get_angle(
                landmark_list[14], landmark_list[12], landmark_list[16]
            )

            # Knee angles
            angles["left_knee"] = get_angle(
                landmark_list[25], landmark_list[23], landmark_list[27]
            )
            angles["right_knee"] = get_angle(
                landmark_list[26], landmark_list[24], landmark_list[28]
            )

            # Hip angles
            angles["left_hip"] = get_angle(
                landmark_list[11], landmark_list[23], landmark_list[25]
            )
            angles["right_hip"] = get_angle(
                landmark_list[12], landmark_list[24], landmark_list[26]
            )

            # Body torso angle (tilt)
            if len(landmark_list) >= 24:
                shoulder_mid = (
                    np.array([landmark_list[11].x + landmark_list[12].x,
                              landmark_list[11].y + landmark_list[12].y]) / 2
                )
                hip_mid = (
                    np.array([landmark_list[23].x + landmark_list[24].x,
                              landmark_list[23].y + landmark_list[24].y]) / 2
                )
                angles["torso_tilt"] = np.abs(
                    np.degrees(np.arctan2(
                        shoulder_mid[1] - hip_mid[1],
                        shoulder_mid[0] - hip_mid[0]
                    ))
                )
        except Exception:
            pass

        return angles

    def _calculate_bbox(self, landmarks, frame_shape) -> Dict[str, int]:
        """
        Calculate bounding box for the pose.

        Args:
            landmarks: MediaPipe pose landmarks
            frame_shape: Shape of the frame (height, width, channels)

        Returns:
            Dictionary with bbox coordinates
        """
        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = 0, 0

        for landmark in landmarks.landmark:
            x = landmark.x * frame_shape[1]
            y = landmark.y * frame_shape[0]

            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

        return {
            "x": int(min_x),
            "y": int(min_y),
            "width": int(max_x - min_x),
            "height": int(max_y - min_y),
        }

    def _calculate_confidence(self, landmarks) -> float:
        """
        Calculate overall confidence score for pose detection.

        Args:
            landmarks: MediaPipe pose landmarks

        Returns:
            Confidence score between 0 and 1
        """
        total_visibility = sum(
            landmark.visibility for landmark in landmarks.landmark
        )
        avg_visibility = total_visibility / len(landmarks.landmark)
        return round(avg_visibility, 2)

    def track_poses_across_frames(
        self, frames_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Track poses across multiple frames.

        Args:
            frames_data: List of frame data dictionaries

        Returns:
            List of pose tracking results
        """
        pose_timeline = []

        for frame_data in frames_data:
            poses = self.detect_poses_in_frame(frame_data)
            pose_timeline.extend(poses)

        return pose_timeline

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input for pose analysis.

        Accepts input with:
            - frames: List of frame data dictionaries
            - frame: Single frame data dictionary

        Args:
            input_data: Dictionary with frame data

        Returns:
            Dictionary with pose analysis results
        """
        if "frames" in input_data:
            frames = input_data["frames"]
            poses = []

            for frame_data in frames:
                frame_poses = self.detect_poses_in_frame(frame_data)
                poses.extend(frame_poses)

            return {"poses": poses, "total_poses": len(poses)}

        elif "frame" in input_data:
            frame = input_data["frame"]
            poses = self.detect_poses_in_frame(frame)
            return {"poses": poses, "total_poses": len(poses)}

        else:
            return {"error": "No frames or frame provided"}

    def cleanup(self) -> None:
        """Clean up MediaPipe resources."""
        super().cleanup()
        if hasattr(self, "pose") and self.pose:
            self.pose.close()
