from typing import List, Dict, Any
from ..core import BaseAgent, Task
from ..tools import WebScraper
from loguru import logger
import asyncio
import re

class WebScraperAgent(BaseAgent):
    def __init__(self, agent_id: str = None, name: str = None):
        super().__init__(agent_id, name or "WebScraperAgent")
        self.scraper = None
    
    def get_capabilities(self) -> List[str]:
        return ["web_scraping", "data_extraction", "content_fetching"]
    
    def _initialize_tools(self):
        """Initialize web scraping tools"""
        self.tools = {
            "scrape_page": self.scrape_page,
            "extract_links": self.extract_links,
            "extract_images": self.extract_images
        }
    
    async def process_task(self, task: Task) -> Any:
        """Optimized web scraping task processing"""
        if not self.scraper:
            self.scraper = WebScraper()
            await self.scraper.__aenter__()
        
        try:
            parameters = task.parameters
            urls = parameters.get("urls", [])
            use_selenium = parameters.get("use_selenium", False)
            
            # Use ZAI to extract URLs if not provided
            if not urls:
                urls = await self._extract_urls_with_zai(task.description)
            
            if not urls:
                # Fallback to regex extraction
                urls = self._extract_urls_regex(task.description)
            
            if not urls:
                raise ValueError("No URLs provided for scraping")
            
            # Scrape with aggressive settings (relaxed ethics)
            results = await self._aggressive_scrape(urls, use_selenium)
            
            # Use ZAI for intelligent content analysis
            analyzed_results = await self._analyze_with_zai(results)
            
            return {
                "scraped_pages": len(analyzed_results),
                "successful_scrapes": len([r for r in analyzed_results if "error" not in r]),
                "results": analyzed_results
            }
            
        except Exception as e:
            logger.error(f"Web scraping failed: {str(e)}")
            raise e
        finally:
            if self.scraper:
                await self.scraper.__aexit__(None, None, None)
                self.scraper = None
    
    async def _extract_urls_with_zai(self, text: str) -> List[str]:
        """Extract URLs using ZAI"""
        if not self.zai_client:
            return []
        
        try:
            prompt = f"""Extract all URLs from this text:
{text}

Return only URLs, one per line."""
            
            response = await self.zai_client.generate_text(prompt, temperature=0.1)
            if response:
                urls = [line.strip() for line in response.split('\n') if line.strip()]
                return [url for url in urls if url.startswith(('http://', 'https://'))]
        except Exception as e:
            logger.warning(f"ZAI URL extraction failed: {str(e)}")
        
        return []
    
    def _extract_urls_regex(self, text: str) -> List[str]:
        """Fallback URL extraction with regex"""
        url_pattern = r'https?://[^\s<>"\'{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
    
    async def _aggressive_scrape(self, urls: List[str], use_selenium: bool = False) -> List[Dict[str, Any]]:
        """Aggressive scraping with relaxed settings"""
        # Override rate limiting for autonomy
        original_delay = self.scraper.rate_limit_delay if hasattr(self.scraper, 'rate_limit_delay') else 0.1
        self.scraper.rate_limit_delay = 0.01  # Very aggressive
        
        try:
            # Scrape with high concurrency
            semaphore = asyncio.Semaphore(20)  # Allow 20 concurrent requests
            
            async def scrape_with_semaphore(url):
                async with semaphore:
                    return await self.scraper.fetch_page(url, use_selenium)
            
            results = await asyncio.gather(
                *[scrape_with_semaphore(url) for url in urls],
                return_exceptions=True
            )
            
            return [r for r in results if isinstance(r, dict)]
            
        finally:
            self.scraper.rate_limit_delay = original_delay
    
    async def _analyze_with_zai(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use ZAI to analyze scraped content"""
        analyzed_results = []
        
        for result in results:
            if isinstance(result, dict) and "error" not in result:
                # Use ZAI for content analysis
                try:
                    content = result.get("text", "")[:1000]  # Limit for ZAI
                    if content and self.zai_client:
                        prompt = f"""Extract key info from this content in 2 bullet points:
{content}"""
                        
                        analysis = await self.zai_client.generate_text(prompt, temperature=0.2)
                        result["zai_analysis"] = analysis
                except Exception as e:
                    logger.warning(f"ZAI analysis failed: {str(e)}")
            
            analyzed_results.append(result)
        
        return analyzed_results
    
    async def scrape_page(self, url: str, use_selenium: bool = False) -> Dict[str, Any]:
        """Scrape a single page"""
        if not self.scraper:
            self.scraper = WebScraper()
            await self.scraper.__aenter__()
        
        return await self.scraper.fetch_page(url, use_selenium)
    
    async def extract_links(self, html_content: str) -> List[str]:
        """Extract links from HTML content"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        return [a.get('href') for a in soup.find_all('a', href=True)]
    
    async def extract_images(self, html_content: str) -> List[str]:
        """Extract image URLs from HTML content"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        return [img.get('src') for img in soup.find_all('img', src=True)]
    
    async def terminate(self):
        """Terminate the agent and cleanup resources"""
        if self.scraper:
            await self.scraper.__aexit__(None, None, None)
        await super().terminate()