# Judo Video Analysis Pipeline

AI-powered judo match analysis using vision-language models. Extracts key frames from video, analyzes techniques, and produces structured match reports.

## Architecture

The pipeline uses a **3-pass analysis** approach:

1. **Pass 1 — Moment Detection**: Scans extracted frames to identify key moments in the match (throws, pins, penalties, etc.).
2. **Pass 2 — Technique Deep-Dive**: Analyzes each detected moment in detail to classify specific techniques, body mechanics, and scoring criteria.
3. **Pass 3 — Match Summary**: Produces a consolidated match report with techniques, scores, and a narrative summary.

For efficiency, frames are batched: **5 images per API request** are sent together to the vision model.

## Setup

### Prerequisites

- Python 3.10+
- OpenCV (`opencv-python`)
- `requests` library

### Install

```bash
pip install -r requirements.txt
```

### Configuration

Copy `config/.env.example` to `config/.env` and set the following environment variables:

| Variable | Description | Default |
|---|---|---|
| `VISION_BASE_URL` | URL of your OpenAI-compatible vision model API | `http://192.168.2.114:8080` |
| `VISION_MODEL` | Model name to use for analysis | `qwen2.5vl` |
| `FRAME_EXTRACTION_MAX_FRAMES` | Maximum frames to extract per video | `25` |
| `SCENE_CHANGE_THRESHOLD` | Threshold for scene change detection | `30` |
| `MOTION_THRESHOLD` | Threshold for motion-based frame selection | `15` |
| `OUTPUT_DIR` | Directory for output reports | `output` |

## Local Vision Model

The pipeline uses an **OpenAI-compatible API** (e.g. a llama.cpp server). Point `VISION_BASE_URL` to your local server.

**Default**: `http://192.168.2.114:8080` with model `qwen2.5vl`.

## Usage

### CLI mode

Run the full pipeline on a video file:

```bash
python -m src.main <video_path>
```

Outputs a JSON report to the `output/` directory.

### API mode

Start the FastAPI server:

```bash
uvicorn api.main:app
```

The server runs at `http://localhost:8000`. Send a video for analysis:

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@path/to/match.mp4"
```

## Output Format

The pipeline produces a JSON report with the `MatchAnalysis` structure:

- **Techniques**: List of detected techniques with timestamps, descriptions, and confidence scores.
- **Scores**: Ippon, Waza-ari, Yuko, and penalty breakdown.
- **Narrative Summary**: Human-readable match summary.

## Project Structure

```
src/           — core pipeline (video processing, LLM analysis, schemas)
api/           — FastAPI server
config/        — .env configuration
scripts/       — utility scripts (e.g. judo.tv downloader)
tests/         — unit tests
```
