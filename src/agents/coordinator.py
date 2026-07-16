"""Coordinator Agent that orchestrates other agents."""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from .base import BaseAgent
from .video_loader import VideoLoaderAgent
from .video_analyst import VideoAnalysisAgent
from .pose_analyst import PoseAnalysisAgent
from .technique_analyst import TechniqueRecognitionAgent
from .strategy_analyst import StrategyAnalysisAgent


class CoordinatorAgent(BaseAgent):
    """Coordinator agent that manages other agents."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Coordinator Agent.

        Args:
            config: Configuration dictionary
        """
        super().__init__("CoordinatorAgent", config)
        self.agents: Dict[str, BaseAgent] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Initialize all sub-agents."""
        # Initialize Video Loader Agent
        self.agents["video_loader"] = VideoLoaderAgent(
            self.config.get("agents", {}).get("video_loader", {})
        )
        self.agents["video_loader"].initialize()

        # Initialize Video Analysis Agent
        self.agents["video_analyzer"] = VideoAnalysisAgent(
            self.config.get("agents", {}).get("video_analyzer", {})
        )
        self.agents["video_analyzer"].initialize()

        # Initialize Pose Analysis Agent
        self.agents["pose_analyzer"] = PoseAnalysisAgent(
            self.config.get("agents", {}).get("pose_analyzer", {})
        )
        self.agents["pose_analyzer"].initialize()

        # Initialize Technique Recognition Agent
        self.agents["technique_analyzer"] = TechniqueRecognitionAgent(
            self.config.get("agents", {}).get("technique_analyzer", {})
        )
        self.agents["technique_analyzer"].initialize()

        # Initialize Strategy Analysis Agent
        self.agents["strategy_analyzer"] = StrategyAnalysisAgent(
            self.config.get("agents", {}).get("strategy_analyzer", {})
        )
        self.agents["strategy_analyzer"].initialize()

        self._initialized = True

    def analyze_video(
        self,
        video_source: str,
        analysis_type: str = "full",
        input_type: str = "url",
    ) -> Dict[str, Any]:
        """
        Analyze a video using all agents.

        Args:
            video_source: Video URL or file path
            analysis_type: Type of analysis ("full", "pose", "technique", "strategy")
            input_type: Type of input ("url" or "path")

        Returns:
            Dictionary with complete analysis results
        """
        if not self._initialized:
            self.initialize()

        result = {
            "video_source": video_source,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "agents": {},
        }

        # Step 1: Load video (if URL)
        video_url = video_source
        if input_type == "url":
            loader_result = self.agents["video_loader"].process({
                "url": video_source
            })
            result["agents"]["video_loader"] = loader_result

            if "videos" not in loader_result or not loader_result["videos"]:
                result["error"] = "No videos found"
                return result

            video_info = loader_result["videos"][0]
            # Prefer local path (downloaded) over remote URL
            video_url = video_info.get("local_path") or video_info.get("video_url", video_source)

        # Step 2: Extract frames (needed for all analysis types)
        video_result = self.agents["video_analyzer"].process({
            "video_path": video_url,
            "action": "extract_frames",
        })
        result["agents"]["video_analyzer"] = video_result

        # Step 3: Pose analysis (needed for "pose", "technique", "strategy", "full")
        if analysis_type in ("pose", "full"):
            pose_result = self.agents["pose_analyzer"].process({
                "frames": video_result.get("frames", []),
            })
            result["agents"]["pose_analyzer"] = pose_result

        # Step 4: Technique recognition (needs pose data)
        if analysis_type in ("technique", "full"):
            pose_result = result.get("agents", {}).get("pose_analyzer", {})
            technique_result = self.agents["technique_analyzer"].process({
                "techniques": [pose_result],
            })
            result["agents"]["technique_analyzer"] = technique_result

        # Step 5: Strategy analysis (needs technique data)
        if analysis_type in ("strategy", "full"):
            technique_result = result.get("agents", {}).get("technique_analyzer", {})
            strategy_result = self.agents["strategy_analyzer"].process({
                "techniques": technique_result.get("sequence", []),
            })
            result["agents"]["strategy_analyzer"] = strategy_result

        # Generate synthesis
        result["synthesis"] = self._generate_synthesis(result)

        return result

    def _generate_synthesis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a synthesized summary of all analysis.

        Args:
            result: Complete analysis result

        Returns:
            Dictionary with synthesized summary
        """
        synthesis = {
            "summary": "",
            "key_findings": [],
            "recommendations": [],
        }

        pose_data = result.get("agents", {}).get("pose_analyzer", {})
        techniques = result.get("agents", {}).get("technique_analyzer", {})
        strategy = result.get("agents", {}).get("strategy_analyzer", {})

        # Extract key findings
        pose_count = pose_data.get("total_poses", 0)
        if pose_count > 0:
            synthesis["key_findings"].append(
                f"Detected {pose_count} pose instances"
            )

        technique_list = techniques.get("sequence", [])
        if technique_list:
            synthesis["key_findings"].append(
                f"Identified {len(technique_list)} technique instances"
            )

        # Generate summary
        if techniques:
            technique_names = [
                t.get("technique", "unknown")
                for t in technique_list
            ]
            synthesis["summary"] = (
                f"Analysis complete. "
                f"Detected {pose_count} poses and identified techniques: "
                f"{', '.join(technique_names[:5])}"
            )

        # Add recommendations
        recommendations = strategy.get("recommendations", [])
        for rec in recommendations[:3]:  # Top 3 recommendations
            synthesis["recommendations"].append({
                "type": rec.get("type", "general"),
                "action": rec.get("action", ""),
            })

        return synthesis

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input using coordinated agents.

        Args:
            input_data: Dictionary with video source and analysis options

        Returns:
            Dictionary with analysis results
        """
        video_source = input_data.get("video_source") or input_data.get("url")
        analysis_type = input_data.get("analysis_type", "full")
        input_type = input_data.get("input_type", "url")

        if not video_source:
            return {
                "error": "No video_source or url provided",
                "usage": "Use --url <video_url> or --video <video_path>",
            }

        return self.analyze_video(video_source, analysis_type, input_type)

    def cleanup(self) -> None:
        """Clean up all sub-agents."""
        super().cleanup()
        for agent in self.agents.values():
            agent.cleanup()
        self.agents.clear()

    def run_full_analysis(
        self,
        video_source: str,
        input_type: str = "url",
        analysis_type: str = "full",
    ) -> Dict[str, Any]:
        """
        Run a complete video analysis.

        Args:
            video_source: Video URL or file path
            input_type: Type of input ("url" or "path")
            analysis_type: Type of analysis ("full", "pose", "technique", "strategy")

        Returns:
            Dictionary with full analysis results
        """
        return self.analyze_video(
            video_source,
            analysis_type=analysis_type,
            input_type=input_type,
        )
