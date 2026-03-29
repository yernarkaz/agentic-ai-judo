# Agentic AI Judo - Implementation Plan

## Context

Building an intelligent AI agent system to analyze videos of professional judo players. The system will use a hybrid agent architecture combining a central coordinator with specialized sub-agents for:

- **Video Loading**: Selenium-based agent to fetch videos from judo.tv
- **Video Analysis**: Extract frames and perform quality assessment
- **Pose Analysis**: Detect and track judo players using MediaPipe
- **Technique Recognition**: Identify judo techniques and evaluate execution
- **Strategy Analysis**: Analyze tactics and generate recommendations

## Target Architecture

```
+--------------------------------------------------+
|              User Interface Layer                |
|  (CLI/Web API/Video Input Handler)              |
+-------------------------+--------------------------+
                        |
                        v
+--------------------------------------------------+
|         Coordinator Agent (Orchestrator)        |
|  - Task decomposition                            |
|  - Agent coordination                            |
|  - Result synthesis                              |
+-------------------------+--------------------------+
                        |
        +---------------+---------------+-----------+
        |               |               |           |
        v               v               v           v
+---------------+  +---------------+  +---------------+  +--------+  +--------+
| Video Loader    |  | Video Analyst |  | Pose Analyst  |  | Technique|  | Strategy|
| Agent (Selenium)|  | Agent         |  | Agent         |  | Agent    |  | Agent   |
+---------------+  +---------------+  +---------------+  +--------+  +--------+
        |               |               |           |
        v               v               v           v
+--------------------------------------------------+
|              Tool Layer                          |
|  - LLMs (Claude/GPT-4o)                         |
|  - OpenCV/MediaPipe for CV                        |
|  - Selenium for judo.tv                          |
|  - Video processing utilities                    |
+--------------------------------------------------+
```


## Technology Stack

| Layer | Technology |
|-------|-----------|
| LLMs | OpenAI GPT-4o / Anthropic Claude (flexible) |
| Computer Vision | OpenCV, MediaPipe Pose |
| Agent Framework | LangGraph |
| Video Loading | Selenium (for judo.tv) |
| API Framework | FastAPI (optional) |
| Video Processing | moviepy, ffmpeg-python |

## Project Structure

```
agentic-ai-judo/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Entry point
│   ├── config.py                  # Configuration
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                # Base Agent class
│   │   ├── coordinator.py         # Coordinator Agent
│   │   ├── video_loader.py        # Selenium-based Video Loader Agent (from judo.tv)
│   │   ├── video_analyst.py       # Video Analysis Agent
│   │   ├── pose_analyst.py        # Pose Analysis Agent
│   │   ├── technique_analyst.py   # Technique Recognition Agent
│   │   └── strategy_analyst.py    # Strategy Analysis Agent
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── selenium_wrapper.py    # Selenium utilities for judo.tv
│   │   ├── video_processor.py     # Video utilities
│   │   ├── pose_estimator.py      # MediaPipe wrapper
│   │   ├── technique_db.py        # Technique database
│   │   └── llm_wrapper.py         # LLM integration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── analysis_result.py     # Result data models
│   │   └── prompts.py             # Prompt templates
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       └── helpers.py
├── data/
│   ├── input/                     # Video files
│   ├── output/                    # Analysis results
│   └── techniques.json            # Technique database
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   └── test_tools.py
├── requirements.txt
└── README.md
```

## Key Agent Responsibilities

### Coordinator Agent
- Accept and parse video analysis requests
- Decompose complex tasks into sub-tasks
- Route tasks to appropriate specialized agents
- Synthesize and format final results (both text report and JSON)

### Video Loader Agent
- Use Selenium to navigate judo.tv
- Search for and select judo videos
- Extract video URLs from judo.tv pages
- Download videos using the extracted URLs
- Handle authentication if required
- Pass video URLs to Video Analysis Agent

### Video Analysis Agent
- Load videos from downloaded files
- Extract frames at specified intervals
- Perform video quality assessment
- Detect scene changes

### Pose Analysis Agent
- Detect and track judo players using MediaPipe
- Extract skeletal keypoint data
- Calculate body angles (knee bend, torso angle, arm extension)
- Track player movement and positioning

### Technique Recognition Agent
- Identify judo techniques (throws, grips, ground work)
- Match movements against technique database
- Label specific techniques (e.g., "Seoi Nage", "O Soto Gari")
- Evaluate technique execution quality

### Strategy Analysis Agent
- Analyze positioning and spacing
- Identify tactical patterns
- Evaluate grip fighting strategies
- Generate strategic recommendations

## Implementation Phases

1. **Foundation**: Project structure, base agent class, Selenium wrapper, configuration
2. **Core Agents**: Video loader (Selenium), Video analysis, Pose analysis, Technique recognition
3. **Advanced Features**: Strategy agent, coordinator agent
4. **Integration & Testing**: End-to-end testing, error handling

## Verification

1. Run tests: `pytest tests/`
2. Test Selenium video loading: `python src/main.py --url https://www.judo.tv/video/... --output data/output/`
3. Verify output contains both text report and structured JSON
