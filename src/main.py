#!/usr/bin/env python3
"""Main entry point for the agentic AI Judo application."""

import argparse
import json
import os
import sys

# Add parent directory to path to enable src imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import config
from src.agents.coordinator import CoordinatorAgent


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Agentic AI Judo - Video Analysis System"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="URL of the video to analyze (from judo.tv)",
    )
    parser.add_argument(
        "--video",
        type=str,
        help="Local video file path to analyze",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/output",
        help="Output directory for results",
    )
    parser.add_argument(
        "--analysis-type",
        type=str,
        default="full",
        choices=["full", "pose", "technique", "strategy"],
        help="Type of analysis to perform",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="both",
        choices=["json", "text", "both"],
        help="Output format",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    return parser.parse_args()


def ensure_output_dir(output_dir: str) -> None:
    """Ensure output directory exists."""
    os.makedirs(output_dir, exist_ok=True)


def save_results(
    results: dict,
    output_dir: str,
    video_source: str,
    output_format: str = "both",
    verbose: bool = False,
    analysis_type: str = "full",
) -> None:
    """
    Save analysis results to files.

    Args:
        results: Analysis results dictionary
        output_dir: Output directory path
        video_source: Source of the video
        output_format: Format to save ("json", "text", or "both")
        verbose: Whether to print save confirmations
        analysis_type: Type of analysis performed
    """
    # Generate filename from video source
    if video_source.startswith("https://"):
        # Extract video ID from URL
        video_id = video_source.split("/")[-1]
    else:
        video_id = os.path.splitext(os.path.basename(video_source))[0]

    # Clean video ID (remove special characters)
    video_id = "".join(c for c in video_id if c.isalnum() or c in "-_")[:50]

    # Save JSON
    if output_format in ("json", "both"):
        json_path = os.path.join(output_dir, f"{video_id}_analysis.json")
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        if verbose:
            print(f"JSON results saved to: {json_path}")

    # Save text report
    if output_format in ("text", "both"):
        text_path = os.path.join(output_dir, f"{video_id}_report.txt")
        with open(text_path, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("AGENTIC AI JUDO - VIDEO ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Video Source: {video_source}\n")
            f.write(f"Analysis Type: {analysis_type}\n")
            f.write(f"Timestamp: {results.get('timestamp', '')}\n\n")

            # Write synthesis
            synthesis = results.get("synthesis", {})
            f.write("SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(synthesis.get("summary", "No summary available") + "\n\n")

            f.write("KEY FINDINGS\n")
            f.write("-" * 40 + "\n")
            for finding in synthesis.get("key_findings", []):
                f.write(f"- {finding}\n")
            f.write("\n")

            f.write("RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            for rec in synthesis.get("recommendations", []):
                f.write(f"- [{rec.get('type', 'general').upper()}] {rec.get('action', '')}\n")
            f.write("\n")

            # Write detailed agent results
            f.write("\nDETAILED ANALYSIS\n")
            f.write("=" * 60 + "\n\n")

            agents = results.get("agents", {})
            for agent_name, agent_result in agents.items():
                f.write(f"\n{agent_name.upper()}\n")
                f.write("-" * 40 + "\n")

                # Convert result to readable format
                result_str = json.dumps(agent_result, indent=2, default=str)
                f.write(result_str[:5000])  # Limit length
                if len(result_str) > 5000:
                    f.write("\n... (truncated)")

        if verbose:
            print(f"Text report saved to: {text_path}")


def main():
    """Main entry point."""
    args = parse_args()

    # Load configuration if provided
    if args.config:
        config._load_config_file(args.config)

    # Ensure output directory exists
    ensure_output_dir(args.output)

    # Initialize coordinator
    coordinator = CoordinatorAgent(config.to_dict())

    try:
        # Determine input type and source
        if args.url:
            input_type = "url"
            video_source = args.url
        elif args.video:
            input_type = "path"
            video_source = args.video
        else:
            print("Error: Please provide --url or --video")
            sys.exit(1)

        # Run analysis
        if args.verbose:
            print(f"Analyzing video: {video_source}")
            print(f"Analysis type: {args.analysis_type}")
            print(f"Output directory: {args.output}")

        results = coordinator.run_full_analysis(
            video_source, input_type, args.analysis_type
        )

        # Save results
        save_results(
            results, args.output, video_source, args.format,
            verbose=args.verbose, analysis_type=args.analysis_type,
        )

        # Print summary
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)

        synthesis = results.get("synthesis", {})
        print(f"\nSummary: {synthesis.get('summary', 'N/A')}")

        if args.verbose:
            print(f"\nResults saved to: {args.output}")

    except Exception as e:
        print(f"Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        coordinator.cleanup()


if __name__ == "__main__":
    main()
