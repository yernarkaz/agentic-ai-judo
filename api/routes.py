import os
import json
import shutil
import glob
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List, Optional
from .models import VideoResponse, AnalysisResult, AnalysisSummary

# Add src to path
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.main import JudoAnalysisPipeline

router = APIRouter()

# Global pipeline instance
_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = JudoAnalysisPipeline(PROJECT_ROOT)
    return _pipeline


@router.post("/upload", response_model=VideoResponse)
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a video and start analysis in the background."""
    data_dir = os.path.join(PROJECT_ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)

    file_path = os.path.join(data_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    pipeline = get_pipeline()
    background_tasks.add_task(pipeline.process_video, file_path)

    return VideoResponse(
        video_id=file.filename,
        filename=file.filename,
        message="Video uploaded and analysis started. Use GET /analyze/{video_id} to check results.",
    )


@router.get("/analyze/{video_id}", response_model=AnalysisResult)
async def get_analysis(video_id: str):
    """Get the full analysis for a video."""
    video_name = os.path.splitext(video_id)[0]
    analysis_dir = os.path.join(PROJECT_ROOT, "output", "analysis", video_name)

    if not os.path.exists(analysis_dir):
        return AnalysisResult(video_id=video_id, status="pending")

    # Find latest JSON analysis
    json_files = glob.glob(os.path.join(analysis_dir, "analysis_*.json"))
    text_files = glob.glob(os.path.join(analysis_dir, "report_*.txt"))

    if not json_files:
        return AnalysisResult(video_id=video_id, status="pending")

    latest_json = max(json_files, key=os.path.getmtime)

    try:
        with open(latest_json, "r") as f:
            analysis_data = json.load(f)

        report_text = None
        if text_files:
            latest_text = max(text_files, key=os.path.getmtime)
            with open(latest_text, "r") as f:
                report_text = f.read()

        return AnalysisResult(
            video_id=video_id,
            status="completed",
            analysis=analysis_data,
            report_text=report_text,
        )
    except Exception as e:
        return AnalysisResult(video_id=video_id, status="error", error=str(e))


@router.get("/analyze/{video_id}/summary", response_model=AnalysisSummary)
async def get_analysis_summary(video_id: str):
    """Get a brief summary of the analysis."""
    video_name = os.path.splitext(video_id)[0]
    analysis_dir = os.path.join(PROJECT_ROOT, "output", "analysis", video_name)

    if not os.path.exists(analysis_dir):
        return AnalysisSummary(video_id=video_id, status="pending")

    json_files = glob.glob(os.path.join(analysis_dir, "analysis_*.json"))
    if not json_files:
        return AnalysisSummary(video_id=video_id, status="pending")

    latest_json = max(json_files, key=os.path.getmtime)

    try:
        with open(latest_json, "r") as f:
            data = json.load(f)

        return AnalysisSummary(
            video_id=video_id,
            status="completed",
            overall_assessment=data.get("overall_assessment"),
            techniques_count=len(data.get("techniques", [])),
            moments_count=len(data.get("moments", [])),
            dominant_techniques=data.get("dominant_techniques"),
            priority_improvements=data.get("priority_improvements"),
        )
    except Exception as e:
        return AnalysisSummary(video_id=video_id, status="error")


@router.get("/videos", response_model=List[str])
async def list_videos():
    """List all videos available for analysis."""
    data_dir = os.path.join(PROJECT_ROOT, "data")
    if not os.path.exists(data_dir):
        return []
    videos = [
        f
        for f in os.listdir(data_dir)
        if f.lower().endswith((".mp4", ".mov", ".avi"))
    ]
    return videos
