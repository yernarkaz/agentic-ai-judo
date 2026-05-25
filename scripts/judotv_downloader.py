#!/usr/bin/env python3
"""
JudoTV Video Downloader for Aldiyar Kargulov (ID: 63734)

Usage:
    python3 scripts/judotv_downloader.py [--download] [--contest CODE]

Options:
    --download      Download videos (default: only list available videos)
    --contest CODE  Download only specific contest (e.g., cont_open_esp2026_0001_m_0060_0023)
    --quality       Quality: 1080, 720 (default), 480
    --output DIR    Output directory (default: data/videos/)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from yt_dlp import YoutubeDL

# Configuration
JUDOKA_ID = 63734
JUDOKA_NAME = "Aldiyar Kargulov"
PROFILE_URL = f"https://judotv.com/judoka/{JUDOKA_ID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.39 Safari/537.36",
}

# Auth token - update this when it expires (expires: 2026-05-25)
AUTH_COOKIE = "AccountLoginTokenV2=eyJhbGciOiJFUzUxMiIsInR5cCI6IkpXVCJ9.eyJJZFVzZXIiOjI2OTIwMSwiRW1haWwiOiJ5ZXJuYXJrYXpAZ21haWwuY29tIiwiTmFtZSI6Illlcm5hciBTbWFndWxvdiIsIkRpc3BsYXlOYW1lIjpudWxsLCJHZW5kZXIiOiJtIiwiZXhwIjoxNzgxMTEyNjc4MjkxLCJMaWtlc0p1ZG8iOmZhbHNlLCJDYW5HZXRGYkxpa2VzIjp0cnVlLCJDYW5HZXRGYkVtYWlsIjp0cnVlLCJJZExvZ2luIjoxNTc4MTI5NywiR3JvdXBzIjoiIiwiUm9sZXMiOiIiLCJBY3RpdmF0ZWQiOnRydWUsIkVtYWlsVmVyaWZpZWQiOnRydWV9.AVtyhWuVXl4aI65C_-7HoS6vUe2rOmYHRYN9hYlG9bULUz9-9oVQEjS-89yhjn7imxB3aMqLCPkJ3HO_xvOIAzCKAcDrTMTosipIUpiSQt05l91A8NjDq4txFF_AYT7MN8BDP7Ep8sn_r5xu7wEaGTcNPLwhkcg57lgiYHJyI-BKheJy"


def get_session():
    """Create authenticated requests session."""
    session = requests.Session()
    session.headers.update(HEADERS)
    session.headers.update({"Cookie": AUTH_COOKIE})
    return session


def extract_contests_from_profile(session: requests.Session) -> list[dict]:
    """Extract all contest codes from Kargulov's profile page."""
    response = session.get(PROFILE_URL)
    response.raise_for_status()

    html = response.text

    # Extract full contest URLs from the profile page
    # Pattern: /competitions/{comp_code}/contests/{contest_code}
    url_pattern = r"/competitions/([a-z0-9_]+)/contests/([a-z0-9_]+)"
    matches = re.findall(url_pattern, html)

    # Deduplicate by contest code, keep first occurrence
    seen = set()
    contests = []
    for comp_code, contest_code in matches:
        if contest_code not in seen:
            seen.add(contest_code)
            contests.append({
                "contest_code": contest_code,
                "competition_code": comp_code,
                "url": f"https://judotv.com/competitions/{comp_code}/contests/{contest_code}",
            })

    # Sort by contest code
    contests.sort(key=lambda c: c["contest_code"])
    return contests


def extract_video_url(session: requests.Session, contest_url: str) -> str | None:
    """Extract video URL from contest page."""
    response = session.get(contest_url)
    response.raise_for_status()

    html = response.text

    # Look for CDN video URL
    url_pattern = r"https://yt-ijf-r2\.b-cdn\.net/[^\"]+"
    urls = re.findall(url_pattern, html)

    if urls:
        # Return the master playlist URL
        for url in urls:
            if "h264_master.m3u8" in url:
                return url

    return None


def extract_contest_info(session: requests.Session, contest_url: str) -> dict:
    """Extract contest metadata from page."""
    response = session.get(contest_url)
    response.raise_for_status()

    html = response.text

    # Extract title (contest name)
    title_match = re.search(r"<title>([^<]+)</title>", html)
    title = title_match.group(1) if title_match else "Unknown"

    # Clean title: remove " - Contest - ... - JudoTV"
    title = re.sub(r"\s*-\s*Contest\s*-\s*.*", "", title)

    return {"title": title}


def download_video(
    video_url: str,
    contest_code: str,
    output_dir: str = "data/videos",
    quality: int = 720,
) -> str | None:
    """Download video using yt-dlp."""
    os.makedirs(output_dir, exist_ok=True)

    # Format selection based on quality
    quality_map = {
        1080: "bestvideo[height=1080]+bestaudio",
        720: "bestvideo[height=720]+bestaudio",
        480: "bestvideo[height=480]+bestaudio",
    }

    format_str = quality_map.get(quality, quality_map[720])
    output_template = os.path.join(output_dir, f"{contest_code}.%(ext)s")

    ydl_opts = {
        "format": format_str,
        "outtmpl": output_template,
        "referer": "https://judotv.com/",
        "user_agent": HEADERS["User-Agent"],
        "cookies": None,  # URL is already signed
        "quiet": False,
        "no_warnings": True,
        "ignoreerrors": True,
        "merge_output_format": "mp4",
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

            # Return the output path
            info = ydl.extract_info(video_url, download=False)
            if info:
                base = output_template.rsplit(".%(ext)s", 1)[0]
                return f"{base}.mp4"
    except Exception as e:
        print(f"  Error downloading: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="JudoTV Video Downloader")
    parser.add_argument("--download", action="store_true", help="Download videos")
    parser.add_argument("--contest", type=str, help="Specific contest code")
    parser.add_argument("--quality", type=int, choices=[1080, 720, 480], default=720, help="Video quality")
    parser.add_argument("--output", type=str, default="data/videos", help="Output directory")
    args = parser.parse_args()

    session = get_session()

    if args.contest:
        # Single contest mode
        parts = args.contest.split("_")
        comp_code = "_".join(parts[:3]) if len(parts) >= 3 else parts[0]
        contest_url = f"https://judotv.com/competitions/{comp_code}/contests/{args.contest}"

        contests = [{
            "contest_code": args.contest,
            "competition_code": comp_code,
            "url": contest_url,
        }]
    else:
        # List all contests from profile
        print(f"Fetching contests for {JUDOKA_NAME} (ID: {JUDOKA_ID})...")
        contests = extract_contests_from_profile(session)
        print(f"Found {len(contests)} contests\n")

    # Process contests
    available = []
    for contest in contests:
        code = contest["contest_code"]
        url = contest["url"]

        print(f"Checking {code}...")

        # Extract video URL
        video_url = extract_video_url(session, url)

        if video_url:
            # Extract contest info
            info = extract_contest_info(session, url)
            title = info["title"]

            print(f"  ✓ Video available: {title}")
            available.append({
                "contest_code": code,
                "title": title,
                "video_url": video_url,
                "contest_url": url,
            })
        else:
            print(f"  ✗ No video available")

    if not available:
        print("\nNo videos available for download.")
        return

    print(f"\n{'='*60}")
    print(f"Available videos: {len(available)}")
    print(f"{'='*60}")

    for i, vid in enumerate(available, 1):
        print(f"{i}. {vid['contest_code']}")
        print(f"   Title: {vid['title']}")

    if args.download:
        print(f"\n{'='*60}")
        print(f"Downloading videos (quality: {args.quality}p)...")
        print(f"{'='*60}\n")

        downloaded = 0
        for vid in available:
            print(f"Downloading: {vid['contest_code']}")
            output_path = download_video(
                vid["video_url"],
                vid["contest_code"],
                args.output,
                args.quality,
            )
            if output_path:
                print(f"  Saved: {output_path}")
                downloaded += 1
            else:
                print(f"  Failed to download")

        print(f"\n{'='*60}")
        print(f"Downloaded: {downloaded}/{len(available)}")
        print(f"{'='*60}")
    else:
        print("\nUse --download flag to download videos.")
        print("Example: python3 scripts/judotv_downloader.py --download --quality 720")


if __name__ == "__main__":
    main()
