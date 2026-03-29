"""Technique database for judo technique matching."""

import json
from typing import List, Dict, Any, Optional


class TechniqueDatabase:
    """Database of judo techniques for matching."""

    def __init__(self, db_path: str = "data/techniques.json"):
        """
        Initialize the technique database.

        Args:
            db_path: Path to the technique database file
        """
        self.db_path = db_path
        self.techniques: List[Dict[str, Any]] = []
        self._load_techniques(db_path)

    def _load_techniques(self, db_path: str) -> None:
        """Load techniques from database file."""
        try:
            with open(db_path, "r") as f:
                self.techniques = json.load(f)
        except FileNotFoundError:
            # Create default techniques database
            self._create_default_techniques()
        except json.JSONDecodeError:
            self.techniques = []

    def _create_default_techniques(self) -> None:
        """Create default techniques database."""
        self.techniques = [
            {
                "name": "Seoi Nage",
                "category": "Throwing",
                "description": "Shoulder throw",
                "features": {
                    "elbow_angles": {"left": 90, "right": 90},
                    "knee_angles": {"left": 120, "right": 120},
                    "hip_angles": {"left": 90, "right": 90},
                    "torso_tilt": 45,
                },
            },
            {
                "name": "O Soto Gari",
                "category": "Throwing",
                "description": "Major outer reap",
                "features": {
                    "elbow_angles": {"left": 120, "right": 120},
                    "knee_angles": {"left": 150, "right": 150},
                    "hip_angles": {"left": 60, "right": 60},
                    "torso_tilt": 30,
                },
            },
            {
                "name": "Uchi Mata",
                "category": "Throwing",
                "description": "Inner thigh throw",
                "features": {
                    "elbow_angles": {"left": 100, "right": 100},
                    "knee_angles": {"left": 130, "right": 130},
                    "hip_angles": {"left": 80, "right": 80},
                    "torso_tilt": 60,
                },
            },
            {
                "name": "Harai Goshi",
                "category": "Throwing",
                "description": "Sweeping hip throw",
                "features": {
                    "elbow_angles": {"left": 110, "right": 110},
                    "knee_angles": {"left": 140, "right": 140},
                    "hip_angles": {"left": 70, "right": 70},
                    "torso_tilt": 50,
                },
            },
        ]
        # Save to file
        try:
            with open(self.db_path, "w") as f:
                json.dump(self.techniques, f, indent=2)
        except Exception:
            pass

    def search_techniques(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for matching techniques.

        Args:
            features: Extracted features from pose data

        Returns:
            List of matching techniques with scores
        """
        matches = []

        for technique in self.techniques:
            score = self._calculate_match_score(technique, features)
            if score > 0.3:  # Minimum match score
                matches.append({
                    "name": technique["name"],
                    "category": technique["category"],
                    "description": technique.get("description", ""),
                    "score": score,
                })

        # Sort by score
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches

    def _calculate_match_score(
        self, technique: Dict[str, Any], features: Dict[str, Any]
    ) -> float:
        """
        Calculate match score between features and technique.

        Args:
            technique: Technique from database
            features: Extracted features

        Returns:
            Match score between 0 and 1
        """
        technique_features = technique.get("features", {})
        score = 0.0
        weight_sum = 0.0

        # Compare elbow angles
        if "elbow_angles" in features and "elbow_angles" in technique_features:
            score += self._compare_angles(
                features["elbow_angles"], technique_features["elbow_angles"]
            )
            weight_sum += 1.0

        # Compare knee angles
        if "knee_angles" in features and "knee_angles" in technique_features:
            score += self._compare_angles(
                features["knee_angles"], technique_features["knee_angles"]
            )
            weight_sum += 1.0

        # Compare hip angles
        if "hip_angles" in features and "hip_angles" in technique_features:
            score += self._compare_angles(
                features["hip_angles"], technique_features["hip_angles"]
            )
            weight_sum += 1.0

        # Compare torso tilt
        if "torso_tilt" in features and "torso_tilt" in technique_features:
            technique_tilt = technique_features["torso_tilt"]
            feature_tilt = features["torso_tilt"]
            tilt_diff = abs(technique_tilt - feature_tilt)
            score += max(0, 1 - (tilt_diff / 90))
            weight_sum += 1.0

        if weight_sum > 0:
            return score / weight_sum
        return 0.0

    def _compare_angles(self, angles1: Dict[str, float], angles2: Dict[str, float]) -> float:
        """
        Compare two angle dictionaries.

        Args:
            angles1: First angle dictionary
            angles2: Second angle dictionary

        Returns:
            Angle match score between 0 and 1
        """
        total_score = 0.0
        count = 0

        for key, value1 in angles1.items():
            if key in angles2:
                value2 = angles2[key]
                diff = abs(value1 - value2)
                score = max(0, 1 - (diff / 180))
                total_score += score
                count += 1

        if count > 0:
            return total_score / count
        return 0.0

    def get_technique(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a technique by name."""
        for technique in self.techniques:
            if technique["name"].lower() == name.lower():
                return technique
        return None

    def get_all_techniques(self) -> List[Dict[str, Any]]:
        """Get all techniques."""
        return self.techniques.copy()

    def cleanup(self) -> None:
        """Clean up resources."""
        self.techniques.clear()
