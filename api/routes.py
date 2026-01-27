import os
import shutil
import glob
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List, Optional
from .models import VideoResponse, AnalysisResult

# Add src to path
import sys
# Assuming api/ is inside project root
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
        # Initialize with project root
        _pipeline = JudoAnalysisPipeline(PROJECT_ROOT)
    return _pipeline

@router.post("/upload", response_model=VideoResponse)
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    data_dir = os.path.join(PROJECT_ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Initialize pipeline if not ready
    pipeline = get_pipeline()
    
    # Process in background
    # process_video is synchronous, so FastAPI runs it in a threadpool
    background_tasks.add_task(pipeline.process_video, file_path)
    
    return VideoResponse(
        video_id=file.filename, # Using filename as ID for simplicity
        filename=file.filename,
        message="Video uploaded and processing started"
    )

@router.get("/analyze/{video_id}", response_model=AnalysisResult)
async def get_analysis(video_id: str):
    # Search for analysis file
    # Pattern: {video_name}_{timestamp}.txt in output/analysis
    # video_id is filename like "myvideo.mp4"
    video_name = os.path.splitext(video_id)[0]
    analysis_dir = os.path.join(PROJECT_ROOT, "output", "analysis")
    
    if not os.path.exists(analysis_dir):
        return AnalysisResult(video_id=video_id, status="pending")
    
    # Find latest file for this video
    pattern = os.path.join(analysis_dir, f"{video_name}_*.txt")
    files = glob.glob(pattern)
    
    if not files:
        return AnalysisResult(video_id=video_id, status="pending")
    
    # Sort by modification time
    latest_file = max(files, key=os.path.getmtime)
    
    try:
        with open(latest_file, "r") as f:
            content = f.read()
        return AnalysisResult(
            video_id=video_id, 
            status="completed", 
            analysis=content,
            file_path=latest_file
        )
    except Exception as e:
        return AnalysisResult(video_id=video_id, status="error", error=str(e))

@router.get("/videos", response_model=List[str])
async def list_videos():
    data_dir = os.path.join(PROJECT_ROOT, "data")
    if not os.path.exists(data_dir):
        return []
    videos = [f for f in os.listdir(data_dir) if f.endswith(('.mp4', '.mov', '.avi'))]
    return videos
