"""Strategy Analysis Agent that analyzes tactics and generates recommendations."""

from typing import List, Dict, Any, Optional

from .base import BaseAgent


class StrategyAnalysisAgent(BaseAgent):
    """Agent responsible for strategy analysis."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Strategy Analysis Agent.

        Args:
            config: Configuration dictionary
        """
        super().__init__("StrategyAnalysisAgent", config)

    def analyze_spacing(self, pose_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze spacing between players.

        Args:
            pose_data: List of pose data dictionaries

        Returns:
            Dictionary with spacing analysis
        """
        if len(pose_data) < 2:
            return {
                "players": len(pose_data),
                "spacing_analysis": "Insufficient data for spacing analysis",
            }

        # Analyze distances between players
        distances = []
        for i, player1 in enumerate(pose_data):
            for j, player2 in enumerate(pose_data):
                if i < j:
                    dist = self._calculate_player_distance(player1, player2)
                    distances.append({
                        "player1": i,
                        "player2": j,
                        "distance": dist,
                    })

        avg_distance = sum(d["distance"] for d in distances) / len(distances) if distances else 0

        return {
            "players": len(pose_data),
            "frame_count": len(pose_data),
            "average_distance": round(avg_distance, 2),
            "min_distance": min((d["distance"] for d in distances), default=0),
            "max_distance": max((d["distance"] for d in distances), default=0),
            "spacing_recommendation": self._generate_spacing_recommendation(avg_distance),
        }

    def _calculate_player_distance(self, player1: Dict, player2: Dict) -> float:
        """
        Calculate distance between two players.

        Args:
            player1: First player's pose data
            player2: Second player's pose data

        Returns:
            Distance value
        """
        # Get center points
        center1 = self._get_player_center(player1)
        center2 = self._get_player_center(player2)

        if center1 and center2:
            # Calculate Euclidean distance
            dx = center1["x"] - center2["x"]
            dy = center1["y"] - center2["y"]
            return (dx**2 + dy**2) ** 0.5

        return 0.0

    def _get_player_center(self, player: Dict) -> Optional[Dict[str, float]]:
        """
        Get the center point of a player.

        Args:
            player: Player's pose data

        Returns:
            Dictionary with x, y coordinates
        """
        landmarks = player.get("landmarks", [])

        if not landmarks:
            # Try bbox
            bbox = player.get("bbox", {})
            if bbox:
                return {
                    "x": bbox.get("x", 0) + bbox.get("width", 0) / 2,
                    "y": bbox.get("y", 0) + bbox.get("height", 0) / 2,
                }
            return None

        # Calculate center from landmarks
        x_sum = 0
        y_sum = 0
        count = 0

        for lm in landmarks:
            x_sum += lm.get("x", 0)
            y_sum += lm.get("y", 0)
            count += 1

        if count > 0:
            return {"x": x_sum / count, "y": y_sum / count}

        return None

    def evaluate_grip_fighting(
        self, frames: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate grip fighting strategies.

        Args:
            frames: List of frame data

        Returns:
            Dictionary with grip analysis
        """
        # Analyze hand positions across frames
        grip_patterns = {
            "over_grip": 0,
            "under_grip": 0,
            "lapel_grip": 0,
            "no_grip": 0,
            "unknown": 0,
        }

        for frame in frames:
            pose_data = frame.get("pose_data", {})
            grip_type = self._analyze_grip_position(pose_data)
            grip_patterns[grip_type] += 1

        total = sum(grip_patterns.values())

        return {
            "total_frames_analyzed": total,
            "grip_patterns": grip_patterns,
            "dominant_grip": max(grip_patterns.keys(), key=lambda k: grip_patterns[k]),
            "grip_recommendation": self._generate_grip_recommendation(grip_patterns),
        }

    def _analyze_grip_position(self, pose_data: Dict) -> str:
        """
        Analyze grip position from pose data.

        Args:
            pose_data: Pose data dictionary

        Returns:
            Grip type classification
        """
        angles = pose_data.get("angles", {})
        landmarks = pose_data.get("landmarks", [])

        # Analyze elbow angles to determine grip type
        left_elbow = angles.get("left_elbow", 180)
        right_elbow = angles.get("right_elbow", 180)

        # Determine grip based on elbow positions
        if left_elbow < 90 or right_elbow < 90:
            return "over_grip"
        elif left_elbow > 150 or right_elbow > 150:
            return "under_grip"
        elif 90 <= left_elbow <= 150 or 90 <= right_elbow <= 150:
            return "lapel_grip"
        else:
            return "no_grip"

    def identify_tactical_patterns(
        self, techniques: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify tactical patterns in technique sequences.

        Args:
            techniques: List of technique predictions

        Returns:
            List of identified patterns
        """
        patterns = []

        # Check for common tactical patterns
        pattern_checks = [
            (self._check_combination_pattern, "Combination Pattern"),
            (self._check_counter_pattern, "Counter Pattern"),
            (self._check_feint_pattern, "Feint Pattern"),
            (self._check_fall_pattern, "Fall Pattern"),
        ]

        for check_func, pattern_name in pattern_checks:
            result = check_func(techniques)
            if result:
                patterns.append(result)

        return patterns

    def _check_combination_pattern(self, techniques: List[Dict]) -> Optional[Dict]:
        """Check for combination patterns."""
        if len(techniques) < 2:
            return None

        # Look for throw sequences
        throw_categories = ["Throwing", "Throw"]
        throws = [t for t in techniques if t.get("category") in throw_categories]

        if len(throws) >= 2:
            return {
                "name": "Combination Pattern",
                "description": "Multiple techniques used in sequence",
                "technique_count": len(throws),
                "confidence": 0.8,
            }

        return None

    def _check_counter_pattern(self, techniques: List[Dict]) -> Optional[Dict]:
        """Check for counter patterns."""
        # Look for defensive techniques followed by attacks
        return None  # Would need more specific pattern detection

    def _check_feint_pattern(self, techniques: List[Dict]) -> Optional[Dict]:
        """Check for feint patterns."""
        # Look for techniques that appear to be feints
        return None  # Would need more specific pattern detection

    def _check_fall_pattern(self, techniques: List[Dict]) -> Optional[Dict]:
        """Check for fall patterns."""
        fall_techniques = ["Ippon Seoi Nage", "Harai Goshi", "O Soto Gari"]
        falls = [t for t in techniques if t.get("technique") in fall_techniques]

        if falls:
            return {
                "name": "Fall Pattern",
                "description": "Recognized throw techniques detected",
                "fall_count": len(falls),
                "confidence": 0.7,
            }

        return None

    def generate_strategy_recommendations(
        self, match_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate strategic recommendations.

        Args:
            match_data: Match analysis data

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Analyze spacing
        spacing = match_data.get("spacing", {})
        avg_dist = spacing.get("average_distance", 0)

        if avg_dist > 0.5:
            recommendations.append({
                "type": "spacing",
                "title": "Close Distance",
                "description": "You're maintaining a good distance for throws",
                "action": "Continue maintaining this distance",
            })
        elif avg_dist > 0:
            recommendations.append({
                "type": "spacing",
                "title": "Adjust Distance",
                "description": "You're either too close or too far",
                "action": "Adjust your stance to create optimal throwing distance",
            })

        # Analyze grip fighting
        grip = match_data.get("grip_fighting", {})
        dominant_grip = grip.get("dominant_grip", "unknown")

        if dominant_grip == "over_grip":
            recommendations.append({
                "type": "grip",
                "title": "Over Grip Strategy",
                "description": "You're using an over grip",
                "action": "Consider varying your grip to prevent opponent from escaping",
            })
        elif dominant_grip == "under_grip":
            recommendations.append({
                "type": "grip",
                "title": "Under Grip Strategy",
                "description": "You're using an under grip",
                "action": "Use under grip to control opponent's movement",
            })

        # Analyze technique diversity
        technique_analysis = match_data.get("technique_analysis", {})
        unique_techniques = technique_analysis.get("unique_techniques", [])

        if len(unique_techniques) <= 2:
            recommendations.append({
                "type": "diversity",
                "title": "Increase Technique Variety",
                "description": "Using only a few techniques",
                "action": "Incorporate additional techniques to keep opponent guessing",
            })

        return recommendations

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input for strategy analysis.

        Args:
            input_data: Dictionary with analysis data

        Returns:
            Dictionary with strategy analysis results
        """
        if "pose_data" in input_data:
            return self.analyze_spacing(input_data["pose_data"])

        elif "frames" in input_data:
            grip_analysis = self.evaluate_grip_fighting(input_data["frames"])
            spacing_analysis = self.analyze_spacing(
                input_data["frames"][0].get("pose_data", []) if input_data["frames"] else []
            )
            return {
                "grip_fighting": grip_analysis,
                "spacing": spacing_analysis,
            }

        elif "techniques" in input_data:
            patterns = self.identify_tactical_patterns(input_data["techniques"])
            return {
                "patterns": patterns,
                "recommendations": self.generate_strategy_recommendations({
                    "technique_analysis": {"unique_techniques": len(patterns)}
                }),
            }

        elif "match_data" in input_data:
            return self.generate_strategy_recommendations(input_data["match_data"])

        else:
            return {"error": "No valid input data provided"}

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
