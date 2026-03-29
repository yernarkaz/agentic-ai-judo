"""Selenium wrapper for video loading from judo.tv."""

import os
import time
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class SeleniumWrapper:
    """Wrapper for Selenium WebDriver with judo.tv-specific functionality."""

    def __init__(
        self,
        headless: bool = True,
        implicit_wait: int = 10,
        page_load_timeout: int = 30,
    ):
        """
        Initialize the Selenium wrapper.

        Args:
            headless: Whether to run browser in headless mode
            implicit_wait: Default implicit wait time in seconds
            page_load_timeout: Page load timeout in seconds
        """
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.page_load_timeout = page_load_timeout
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None

    def initialize(self) -> None:
        """Initialize the WebDriver."""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")

        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(self.implicit_wait)
        self.driver.set_page_load_timeout(self.page_load_timeout)
        self.wait = WebDriverWait(self.driver, self.implicit_wait)

    def navigate_to_url(self, url: str) -> bool:
        """
        Navigate to a URL.

        Args:
            url: The URL to navigate to

        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            raise RuntimeError("WebDriver not initialized. Call initialize() first.")

        try:
            self.driver.get(url)
            return True
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            return False

    def wait_for_element(self, locator: tuple, timeout: int = 10) -> Any:
        """
        Wait for an element to be present.

        Args:
            locator: Tuple of (By method, locator string)
            timeout: Maximum wait time in seconds

        Returns:
            WebElement if found, None otherwise
        """
        if not self.wait:
            raise RuntimeError("WebDriver not initialized.")

        try:
            return self.wait.until(EC.presence_of_element_located(locator))
        except Exception:
            return None

    def find_elements(self, locator: tuple) -> List[Any]:
        """
        Find multiple elements by locator.

        Args:
            locator: Tuple of (By method, locator string)

        Returns:
            List of matching WebElements
        """
        if not self.driver:
            raise RuntimeError("WebDriver not initialized.")

        try:
            return self.driver.find_elements(*locator)
        except Exception:
            return []

    def find_element(self, locator: tuple) -> Any:
        """
        Find a single element by locator.

        Args:
            locator: Tuple of (By method, locator string)

        Returns:
            WebElement if found, None otherwise
        """
        elements = self.find_elements(locator)
        return elements[0] if elements else None

    def get_video_urls_from_page(self, url: str) -> List[str]:
        """
        Extract video URLs from a judo.tv page.

        Args:
            url: The page URL to scrape

        Returns:
            List of video URLs found on the page
        """
        if not self.navigate_to_url(url):
            return []

        # Try to find video links - adjust selectors based on judo.tv structure
        video_selectors = [
            (By.CSS_SELECTOR, "a[href*='/video/']"),
            (By.CSS_SELECTOR, ".video-card a"),
            (By.CSS_SELECTOR, "a.video-link"),
        ]

        video_urls = set()
        for selector in video_selectors:
            elements = self.find_elements(selector)
            for elem in elements:
                href = elem.get_attribute("href")
                if href and href.startswith("https://www.judo.tv/video/"):
                    video_urls.add(href)

        return list(video_urls)

    def search_videos(self, query: str) -> List[str]:
        """
        Search for videos on judo.tv.

        Args:
            query: Search query string

        Returns:
            List of video URLs matching the search
        """
        search_url = f"https://www.judo.tv/search?q={query.replace(' ', '%20')}"

        if not self.navigate_to_url(search_url):
            return []

        # Wait for results to load
        time.sleep(2)

        # Extract video links from search results
        return self.get_video_urls_from_page(search_url)

    def extract_video_info(self, video_url: str) -> Dict[str, Any]:
        """
        Extract information from a video page.

        Args:
            video_url: The URL of the video page

        Returns:
            Dictionary containing video information
        """
        if not self.navigate_to_url(video_url):
            return {"url": video_url, "error": "Failed to load page"}

        info = {"url": video_url}

        # Try to extract video title
        title_selectors = [
            (By.CSS_SELECTOR, "h1"),
            (By.CSS_SELECTOR, ".video-title"),
            (By.CSS_SELECTOR, "meta[property='og:title']"),
        ]

        for selector in title_selectors:
            element = self.find_element(selector)
            if element:
                if element.tag_name == "meta":
                    info["title"] = element.get_attribute("content")
                else:
                    info["title"] = element.text
                break

        # Try to extract video source URL
        video_selectors = [
            (By.CSS_SELECTOR, "video source"),
            (By.CSS_SELECTOR, "video"),
            (By.CSS_SELECTOR, ".video-player source"),
        ]

        for selector in video_selectors:
            element = self.find_element(selector)
            if element:
                src = element.get_attribute("src")
                if src:
                    info["video_url"] = src
                break

        return info

    def quit(self) -> None:
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None

    def __enter__(self) -> "SeleniumWrapper":
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.quit()
