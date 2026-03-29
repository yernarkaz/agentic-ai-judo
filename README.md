# Agentic AI Judo

An intelligent AI agent system to analyze videos of professional judo players.

## Overview

This project uses a hybrid agent architecture combining specialized agents for:
- **Video Loading**: Selenium-based agent to fetch videos from judo.tv
- **Video Analysis**: Extract frames and perform quality assessment
- **Pose Analysis**: Detect and track judo players using MediaPipe
- **Technique Recognition**: Identify judo techniques and evaluate execution
- **Strategy Analysis**: Analyze tactics and generate recommendations

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd agentic-ai-judo

# Install dependencies
pip install -r requirements.txt
```

## Usage

### From URL (judo.tv)

```bash
python src/main.py --url https://www.judo.tv/video/... --output data/output/
```

### From Local File

```bash
python src/main.py --video path/to/video.mp4 --output data/output/
```

### Analysis Types

- `--analysis-type full` - Complete analysis (default)
- `--analysis-type pose` - Pose analysis only
- `--analysis-type technique` - Technique recognition only
- `--analysis-type strategy` - Strategy analysis only

### Output Formats

- `--format json` - JSON output only
- `--format text` - Text report only
- `--format both` - Both JSON and text (default)

## Configuration

Create a `config.json` file:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o"
  },
  "video": {
    "frame_interval": 30
  },
  "pose": {
    "confidence_threshold": 0.5
  }
}
```

## Project Structure

```
agentic-ai-judo/
├── src/
│   ├── agents/         # Agent implementations
│   │   ├── base.py
│   │   ├── coordinator.py
│   │   ├── video_loader.py
│   │   ├── video_analyst.py
│   │   ├── pose_analyst.py
│   │   ├── technique_analyst.py
│   │   └── strategy_analyst.py
│   ├── tools/          # Utility tools
│   │   ├── selenium_wrapper.py
│   │   ├── technique_db.py
│   │   └── ...
│   ├── models/         # Data models
│   ├── utils/          # Helper functions
│   └── main.py         # Entry point
├── data/
│   ├── input/          # Video files
│   ├── output/         # Analysis results
│   └── techniques.json # Technique database
├── tests/
└── requirements.txt
```

## License

MIT License
