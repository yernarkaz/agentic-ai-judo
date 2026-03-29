"""Technique Recognition Agent that identifies judo techniques."""

import json
from typing import List, Dict, Any, Optional

from .base import BaseAgent
from ..tools.technique_db import TechniqueDatabase


class TechniqueRecognitionAgent(BaseAgent):
    """Agent responsible for recognizing judo techniques."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Technique Recognition Agent.

        Args:
            config: Configuration dictionary with options:
                - technique_db_path: Path to technique database
        """
        super().__init__("TechniqueRecognitionAgent", config)

        db_path = self.config.get(
            "technique_db_path", "data/techniques.json"
        )
        self.technique_db = TechniqueDatabase(db_path)

    def identify_technique(
        self, pose_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Identify the technique from pose data.

        Args:
            pose_data: Dictionary containing pose landmarks and angles

        Returns:
            Dictionary with technique prediction
        """
        # Extract features from pose data
        angles = pose_data.get("angles", {})
        landmarks = pose_data.get("landmarks", [])

        # Extract key features for technique recognition
        features = self._extract_features(angles, landmarks)

        # Search technique database
        matches = self.technique_db.search_techniques(features)

        if matches:
            return {
                "technique": matches[0]["name"],
                "category": matches[0]["category"],
                "confidence": matches[0]["score"],
                "matched_features": features,
                "matches": matches,
            }
        else:
            return {
                "technique": "unknown",
                "category": "unknown",
                "confidence": 0.0,
                "matched_features": features,
                "matches": [],
            }

    def _extract_features(self, angles: Dict[str, float], landmarks: List[Dict]) -> Dict[str, Any]:
        """
        Extract features from pose data for technique matching.

        Args:
            angles: Dictionary of body angles
            landmarks: List of landmark data

        Returns:
            Dictionary of extracted features
        """
        features = {}

        # Analyze limb positions
        features["elbow_angles"] = {
            "left": angles.get("left_elbow", -1),
            "right": angles.get("right_elbow", -1),
        }
        features["knee_angles"] = {
            "left": angles.get("left_knee", -1),
            "right": angles.get("right_knee", -1),
        }
        features["hip_angles"] = {
            "left": angles.get("left_hip", -1),
            "right": angles.get("right_hip", -1),
        }
        features["torso_tilt"] = angles.get("torso_tilt", 0)

        # Analyze landmark positions
        if landmarks:
            # Get shoulder and hip positions
            shoulder_y = []
            hip_y = []
            knee_y = []

            for lm in landmarks:
                if lm.get("landmark_id") in [11, 12]:  # Shoulders
                    shoulder_y.append(lm.get("y", 0))
                elif lm.get("landmark_id") in [23, 24]:  # Hips
                    hip_y.append(lm.get("y", 0))
                elif lm.get("landmark_id") in [25, 26]:  # Knees
                    knee_y.append(lm.get("y", 0))

            if shoulder_y and hip_y:
                features["body_alignment"] = {
                    "shoulder_y_avg": sum(shoulder_y) / len(shoulder_y),
                    "hip_y_avg": sum(hip_y) / len(hip_y),
                    "knee_y_avg": sum(knee_y) / len(knee_y) if knee_y else 0,
                    "stance_width": self._calculate_stance_width(landmarks),
                }

        return features

    def _calculate_stance_width(self, landmarks: List[Dict]) -> float:
        """Calculate the width of the stance."""
        left_x = None
        right_x = None

        for lm in landmarks:
            if lm.get("landmark_id") == 11:  # Left shoulder
                left_x = lm.get("x", 0)
            elif lm.get("landmark_id") == 12:  # Right shoulder
                right_x = lm.get("x", 0)

        if left_x is not None and right_x is not None:
            return abs(right_x - left_x)

        # Fallback: use hips
        for lm in landmarks:
            if lm.get("landmark_id") == 23:  # Left hip
                left_x = lm.get("x", 0)
            elif lm.get("landmark_id") == 24:  # Right hip
                right_x = lm.get("x", 0)

        if left_x is not None and right_x is not None:
            return abs(right_x - left_x)

        return 0.0

    def match_technique_sequence(
        self, techniques: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze a sequence of techniques.

        Args:
            techniques: List of technique predictions

        Returns:
            Dictionary with sequence analysis
        """
        if not techniques:
            return {
                "sequence": [],
                "total_techniques": 0,
                "patterns_found": [],
                "recommendations": [],
            }

        # Identify patterns
        patterns = self._identify_patterns(techniques)

        # Generate recommendations
        recommendations = self._generate_recommendations(patterns, techniques)

        return {
            "sequence": techniques,
            "total_techniques": len(techniques),
            "patterns_found": patterns,
            "recommendations": recommendations,
        }

    def _identify_patterns(
        self, techniques: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify patterns in technique sequences.

        Args:
            techniques: List of technique predictions

        Returns:
            List of pattern dictionaries
        """
        patterns = []

        # Look for common judo sequences
        throw_sequences = [
            (["Seoi Nage", "Harai Goshi", "O Soto Gari"], "Throw Combo"),
            (["Uchi Mata", "Seoi Nage"], "Throw Sequence"),
        ]

        for tech in techniques:
            technique_name = tech.get("technique", "").lower()

            for pattern_techniques, pattern_name in throw_sequences:
                pattern_lower = [t.lower() for t in pattern_techniques]
                if technique_name in pattern_lower:
                    patterns.append({
                        "name": pattern_name,
                        "matched_technique": tech.get("technique"),
                        "confidence": tech.get("confidence", 0),
                    })

        return patterns

    def _generate_recommendations(
        self, patterns: List[Dict], techniques: List[Dict]
    ) -> List[Dict[str, str]]:
        """
        Generate recommendations based on technique analysis.

        Args:
            patterns: List of identified patterns
            techniques: List of technique predictions

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        if not techniques:
            return recommendations

        # Analyze technique diversity
        unique_techniques = set(
            t.get("technique", "") for t in techniques
        )

        if len(unique_techniques) <= 2:
            recommendations.append({
                "type": "diversity",
                "title": "Increase Technique Variety",
                "description": "Consider learning additional techniques to improve versatility",
                "suggested_techniques": ["Uchi Mata", "Kouchi Gari", "De Ashi Barai"],
            })

        # Analyze technique quality
        low_confidence = [
            t for t in techniques if t.get("confidence", 1.0) < 0.5
        ]

        if low_confidence:
            recommendations.append({
                "type": "quality",
                "title": "Improve Technique Execution",
                "description": f"{len(low_confidence)} techniques had low confidence scores",
                "suggested_practice": "Review form with slow-motion video analysis",
            })

        # Add pattern-based recommendations
        for pattern in patterns:
            if pattern.get("name") == "Throw Combo":
                recommendations.append({
                    "type": "combo",
                    "title": "Effective Throw Combo Detected",
                    "description": "Good combination of throws detected",
                    "suggested_follow_up": "Practice transition techniques",
                })

        return recommendations

    def evaluate_execution_quality(
        self, technique: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate the quality of a technique execution.

        Args:
            technique: Technique prediction dictionary

        Returns:
            Dictionary with quality evaluation
        """
        confidence = technique.get("confidence", 0)

        # Determine quality score
        if confidence >= 0.8:
            quality_score = "excellent"
            score = 90
        elif confidence >= 0.6:
            quality_score = "good"
            score = 70
        elif confidence >= 0.4:
            quality_score = "fair"
            score = 50
        elif confidence >= 0.2:
            quality_score = "poor"
            score = 30
        else:
            quality_score = "unknown"
            score = 10

        return {
            "technique": technique.get("technique", "unknown"),
            "quality_score": quality_score,
            "numeric_score": score,
            "confidence": confidence,
            "feedback": self._generate_feedback(quality_score, technique),
        }

    def _generate_feedback(
        self, quality_score: str, technique: Dict[str, Any]
    ) -> str:
        """Generate feedback based on quality score."""
        feedback_map = {
            "excellent": "Excellent technique execution! Good form and timing.",
            "good": "Good execution. Consider refining specific details.",
            "fair": "Average execution. Focus on fundamentals.",
            "poor": "Needs improvement. Review technique fundamentals.",
            "unknown": "Insufficient data for quality assessment.",
        }
        return feedback_map.get(quality_score, "Review technique execution.")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input for technique recognition.

        Accepts input with:
            - pose_data: Pose data dictionary
            - techniques: List of technique predictions (for sequence analysis)

        Args:
            input_data: Dictionary with technique data

        Returns:
            Dictionary with technique recognition results
        """
        if "pose_data" in input_data:
            return self.identify_technique(input_data["pose_data"])
        elif "techniques" in input_data:
            return self.match_technique_sequence(input_data["techniques"])
        else:
            return {"error": "No pose_data or techniques provided"}

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        self.technique_db.cleanup()
