# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic AI Judo is an intelligent AI agent system that analyzes videos of professional judo players. It uses a hybrid multi-agent architecture combining computer vision (MediaPipe) with LLM-based analysis to detect poses, recognize judo techniques, and provide strategic insights.

## Architecture

### Multi-Agent System

The system uses a coordinator pattern with five specialized agents:

1. **CoordinatorAgent** (`src/agents/coordinator.py`) - Orchestrates all other agents, manages the analysis pipeline, and synthesizes results
2. **VideoLoaderAgent** (`src/agents/video_loader.py`) - Uses Selenium to fetch videos from judo.tv
3. **VideoAnalysisAgent** (`src/agents/video_analyst.py`) - Extracts frames and performs quality assessment
4. **PoseAnalysisAgent** (`src/agents/pose_analyst.py`) - Detects and tracks judo players using MediaPipe
5. **TechniqueRecognitionAgent** (`src/agents/technique_analyst.py`) - Matches pose data to known judo techniques
6. **StrategyAnalysisAgent** (`src/agents/strategy_analyst.py`) - Analyzes tactics and generates recommendations

### Agent Pipeline Flow

```
Video Source (URL/path)
    ↓
VideoLoaderAgent (if URL) → extracts video URLs from judo.tv
    ↓
VideoAnalysisAgent → extracts frames at configurable intervals
    ↓
PoseAnalysisAgent → detects keypoints using MediaPipe
    ↓
TechniqueRecognitionAgent → matches poses to technique database
    ↓
StrategyAnalysisAgent → identifies patterns and generates recommendations
    ↓
CoordinatorAgent → synthesizes results into final report
```

### Key Components

- **BaseAgent** (`src/agents/base.py`) - Abstract base class defining the agent interface (`process()`, `initialize()`, `cleanup()`)
- **Config** (`src/config.py`) - Centralized configuration with dot-notation access (e.g., `config.get("llm.model")`)
- **TechniqueDatabase** (`src/tools/technique_db.py`) - JSON-based technique library with angle-based matching
- **SeleniumWrapper** (`src/tools/selenium_wrapper.py`) - Browser automation for judo.tv scraping

## Commands

### Installation

```bash
pip install -r requirements.txt
```

### Running Analysis

**From judo.tv URL:**
```bash
python src/main.py --url https://www.judo.tv/video/... --output data/output/
```

**From local video file:**
```bash
python src/main.py --video path/to/video.mp4 --output data/output/
```

### Analysis Types

- `--analysis-type full` - Complete pipeline (default)
- `--analysis-type pose` - Pose analysis only
- `--analysis-type technique` - Technique recognition only
- `--analysis-type strategy` - Strategy analysis only

### Output Formats

- `--format json` - JSON output only
- `--format text` - Text report only
- `--format both` - Both JSON and text (default)

### Configuration

Create a `config.json` file to override defaults:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.0
  },
  "video": {
    "frame_interval": 30
  },
  "pose": {
    "confidence_threshold": 0.5
  }
}
```

Then run with: `--config path/to/config.json`

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_pose_analyst.py

# Run with verbose output
pytest -v tests/

# Run specific test function
pytest tests/test_pose_analyst.py::test_pose_detection
```

## Key Implementation Details

### Configuration System

The `Config` class uses dot-notation for nested access:
- `config.get("llm.provider")` → "openai"
- `config.get("pose.confidence_threshold")` → 0.5
- `config.get("paths.data_output")` → "data/output"

Configuration merges recursively - user config overrides defaults.

### Technique Matching

The `TechniqueDatabase` matches poses to techniques by comparing:
- Elbow angles (left/right)
- Knee angles (left/right)
- Hip angles (left/right)
- Torso tilt

Match scores are normalized (0-1) and techniques with score > 0.3 are returned, sorted by score.

### Agent State Management

All agents follow the lifecycle:
1. `initialize()` - Set up resources (Selenium browser, MediaPipe models, etc.)
2. `process(input_data)` - Process input and return results
3. `cleanup()` - Release resources

The CoordinatorAgent manages the lifecycle of all sub-agents.

### Data Paths

- `data/input/` - Input video files
- `data/output/` - Analysis results
- `data/techniques.json` - Technique database (auto-created with defaults if missing)

## Dependencies

- **LLM**: openai, anthropic (configurable provider)
- **Vision**: opencv-python, mediapipe, moviepy
- **Web**: selenium, webdriver-manager
- **Framework**: pydantic, langchain, langgraph
- **Testing**: pytest, pytest-asyncio

## Important Notes

- Selenium requires Chrome/Chromium browser installed
- MediaPipe requires CPU/GPU acceleration support
- Video analysis is computationally intensive
- The technique database starts with 4 default techniques (Seoi Nage, O Soto Gari, Uchi Mata, Harai Goshi)
