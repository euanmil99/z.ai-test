import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from fake_useragent import UserAgent
from typing import Dict, List, Any, Optional
import time
import json
from urllib.parse import urljoin, urlparse
from loguru import logger
from ..config import settings

class WebScraper:
    def __init__(self):
        self.session = None
        self.driver = None
        self.ua = UserAgent()
        self.request_count = 0
        self.last_request_time = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.request_timeout),
            headers={'User-Agent': self.ua.random}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < settings.rate_limit_delay:
            time.sleep(settings.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    async def fetch_page(self, url: str, use_selenium: bool = False) -> Dict[str, Any]:
        """Fetch a web page and return its content"""
        self._rate_limit()
        
        try:
            if use_selenium:
                return await self._fetch_with_selenium(url)
            else:
                return await self._fetch_with_requests(url)
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return {"error": str(e), "url": url}
    
    async def _fetch_with_requests(self, url: str) -> Dict[str, Any]:
        """Fetch page using requests/aiohttp"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    return {
                        "url": url,
                        "status_code": response.status,
                        "content": content,
                        "title": soup.title.string if soup.title else "",
                        "text": soup.get_text(strip=True),
                        "links": [a.get('href') for a in soup.find_all('a', href=True)],
                        "images": [img.get('src') for img in soup.find_all('img', src=True)],
                        "metadata": {
                            "content_type": response.headers.get('content-type', ''),
                            "content_length": response.headers.get('content-length', ''),
                            "last_modified": response.headers.get('last-modified', '')
                        }
                    }
                else:
                    return {"error": f"HTTP {response.status}", "url": url}
                    
        except Exception as e:
            return {"error": str(e), "url": url}
    
    async def _fetch_with_selenium(self, url: str) -> Dict[str, Any]:
        """Fetch page using Selenium for dynamic content"""
        if not self.driver:
            await self._init_selenium()
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, settings.selenium_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page source after JavaScript execution
            content = self.driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
            
            return {
                "url": url,
                "status_code": 200,  # Selenium doesn't give status codes easily
                "content": content,
                "title": soup.title.string if soup.title else "",
                "text": soup.get_text(strip=True),
                "links": [a.get('href') for a in soup.find_all('a', href=True)],
                "images": [img.get('src') for img in soup.find_all('img', src=True)],
                "dynamic_content": True
            }
            
        except TimeoutException:
            return {"error": "Page load timeout", "url": url}
        except WebDriverException as e:
            return {"error": str(e), "url": url}
    
    async def _init_selenium(self):
        """Initialize Selenium WebDriver"""
        options = Options()
        if settings.selenium_headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(f"--user-agent={self.ua.random}")
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(settings.selenium_timeout)
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {str(e)}")
            raise
    
    async def scrape_multiple_pages(self, urls: List[str], use_selenium: bool = False) -> List[Dict[str, Any]]:
        """Scrape multiple pages concurrently"""
        tasks = [self.fetch_page(url, use_selenium) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def search_and_scrape(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search for a query and scrape the top results"""
        # This would integrate with a search API
        # For now, we'll use a simple implementation
        search_urls = await self._get_search_results(query, num_results)
        return await self.scrape_multiple_pages(search_urls)
    
    async def _get_search_results(self, query: str, num_results: int) -> List[str]:
        """Get search result URLs for a query"""
        # Simplified implementation - in practice, you'd use a proper search API
        # For demo purposes, we'll return some common sites
        dummy_results = [
            "https://example.com",
            "https://httpbin.org/html",
            "https://jsonplaceholder.typicode.com"
        ]
        return dummy_results[:num_results]

class SearchEngine:
    def __init__(self):
        self.scraper = WebScraper()
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Perform web search and return results"""
        # This would integrate with DuckDuckGo or another free search API
        # For now, we'll simulate search results
        
        await self.scraper.__aenter__()
        
        try:
            # Simulate search results
            results = [
                {
                    "title": f"Search result {i+1} for '{query}'",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"This is a sample snippet for search result {i+1}",
                    "rank": i+1
                }
                for i in range(min(num_results, 5))  # Limit to 5 for demo
            ]
            
            return results
            
        finally:
            await self.scraper.__aexit__(None, None, None)

class APIClient:
    def __init__(self):
        self.session = None
        self.ua = UserAgent()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.request_timeout),
            headers={'User-Agent': self.ua.random}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to an API"""
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.content_type == 'application/json':
                    data = await response.json()
                else:
                    data = await response.text()
                
                return {
                    "status_code": response.status,
                    "data": data,
                    "headers": dict(response.headers),
                    "url": url
                }
                
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            return {"error": str(e), "url": url}
    
    async def get_json(self, url: str, params: Dict = None) -> Dict[str, Any]:
        """Make a GET request and expect JSON response"""
        return await self.make_request("GET", url, params=params)
    
    async def post_json(self, url: str, data: Dict = None) -> Dict[str, Any]:
        """Make a POST request with JSON data"""
        return await self.make_request("POST", url, json=data)