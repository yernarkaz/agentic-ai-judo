"""Video Loader Agent that uses Selenium to fetch videos from judo.tv."""

from typing import List, Dict, Any, Optional
import os

from .base import BaseAgent
from ..tools.selenium_wrapper import SeleniumWrapper


class VideoLoaderAgent(BaseAgent):
    """Agent responsible for loading videos from judo.tv using Selenium."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Video Loader Agent.

        Args:
            config: Configuration dictionary with options:
                - website: The website to load videos from (default: "judo.tv")
                - headless: Whether to run browser in headless mode
                - search_queries: List of search terms to use
        """
        super().__init__("VideoLoaderAgent", config)
        self.selenium: Optional[SeleniumWrapper] = None
        self.downloaded_videos: List[Dict[str, Any]] = []

    def initialize(self) -> None:
        """Initialize the Selenium wrapper."""
        super().initialize()
        headless = self.config.get("headless", True)
        self.selenium = SeleniumWrapper(headless=headless)
        self.selenium.initialize()

    def load_videos_from_url(self, url: str) -> List[Dict[str, Any]]:
        """
        Load videos from a specific judo.tv URL.

        Args:
            url: The URL to load videos from

        Returns:
            List of video information dictionaries
        """
        if not self.selenium:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        video_urls = self.selenium.get_video_urls_from_page(url)
        videos = []

        for video_url in video_urls:
            info = self.selenium.extract_video_info(video_url)
            info["source_url"] = video_url
            videos.append(info)

        self.downloaded_videos.extend(videos)
        return videos

    def search_videos(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for videos using a query.

        Args:
            query: Search query string

        Returns:
            List of video information dictionaries
        """
        if not self.selenium:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        video_urls = self.selenium.search_videos(query)
        videos = []

        for video_url in video_urls:
            info = self.selenium.extract_video_info(video_url)
            info["source_url"] = video_url
            info["search_query"] = query
            videos.append(info)

        self.downloaded_videos.extend(videos)
        return videos

    def search_multiple(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Search for videos using multiple queries.

        Args:
            queries: List of search query strings

        Returns:
            List of video information dictionaries
        """
        all_videos = []
        for query in queries:
            videos = self.search_videos(query)
            all_videos.extend(videos)
        return all_videos

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input to load videos.

        Accepts input with either:
            - url: Load videos from a specific page
            - query: Search for videos
            - queries: Search with multiple queries

        Args:
            input_data: Dictionary with loading instructions

        Returns:
            Dictionary with videos and metadata
        """
        result = {"videos": [], "count": 0, "source": None}

        if "url" in input_data:
            url = input_data["url"]
            result["source"] = url
            result["videos"] = self.load_videos_from_url(url)

        elif "query" in input_data:
            query = input_data["query"]
            result["source"] = f"search: {query}"
            result["videos"] = self.search_videos(query)

        elif "queries" in input_data:
            queries = input_data["queries"]
            result["source"] = f"search: {', '.join(queries)}"
            result["videos"] = self.search_multiple(queries)

        else:
            result["error"] = "No url, query, or queries provided"

        result["count"] = len(result["videos"])
        return result

    def cleanup(self) -> None:
        """Clean up Selenium resources."""
        super().cleanup()
        if self.selenium:
            self.selenium.quit()
            self.selenium = None

    def get_downloaded_videos(self) -> List[Dict[str, Any]]:
        """Get list of all downloaded videos."""
        return self.downloaded_videos.copy()

    def clear_downloaded(self) -> None:
        """Clear the list of downloaded videos."""
        self.downloaded_videos.clear()
