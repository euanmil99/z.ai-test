from typing import List, Dict, Any
from ..core import BaseAgent, Task
from ..tools import SearchEngine, WebScraper
from loguru import logger
import asyncio

class ResearchAgent(BaseAgent):
    def __init__(self, agent_id: str = None, name: str = None):
        super().__init__(agent_id, name or "ResearchAgent")
        self.search_engine = None
        self.scraper = None
    
    def get_capabilities(self) -> List[str]:
        return ["research", "information_synthesis", "data_analysis", "search"]
    
    def _initialize_tools(self):
        """Initialize research tools"""
        self.tools = {
            "search": self.search_web,
            "analyze_content": self.analyze_content,
            "summarize": self.summarize_content
        }
    
    async def process_task(self, task: Task) -> Any:
        """Optimized research task processing"""
        if not self.search_engine:
            self.search_engine = SearchEngine()
        
        try:
            parameters = task.parameters
            query = parameters.get("query", task.description)
            num_results = parameters.get("num_results", 20)  # Increased for autonomy
            depth = parameters.get("depth", 2)
            
            # Use ZAI to optimize search query
            optimized_query = await self._optimize_query_with_zai(query)
            
            # Step 1: Aggressive search
            search_results = await self._aggressive_search(optimized_query, num_results)
            
            if not search_results:
                return {"error": "No search results found", "query": optimized_query}
            
            # Step 2: Intelligent content scraping and analysis
            detailed_analysis = await self._intelligent_analysis(search_results, depth)
            
            # Step 3: ZAI-powered synthesis
            research_summary = await self._synthesize_with_zai(optimized_query, search_results, detailed_analysis)
            
            return {
                "query": optimized_query,
                "search_results_count": len(search_results),
                "detailed_analysis_count": len(detailed_analysis),
                "summary": research_summary,
                "sources": search_results,
                "detailed_sources": detailed_analysis,
                "research_depth": depth
            }
            
        except Exception as e:
            logger.error(f"Research task failed: {str(e)}")
            raise e
    
    async def _optimize_query_with_zai(self, query: str) -> str:
        """Optimize search query using ZAI"""
        if not self.zai_client:
            return query
        
        try:
            prompt = f"""Improve this search query for better results:
{query}

Return optimized query only."""
            
            optimized = await self.zai_client.generate_text(prompt, temperature=0.2)
            return optimized or query
        except Exception as e:
            logger.warning(f"Query optimization failed: {str(e)}")
            return query
    
    async def _aggressive_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Aggressive search with multiple strategies"""
        all_results = []
        
        # Multiple search strategies
        search_variations = [
            query,
            f"{query} tutorial",
            f"{query} guide",
            f"how to {query}",
            f"{query} examples"
        ]
        
        # Search with variations
        for variation in search_variations[:3]:  # Limit to avoid overloading
            try:
                results = await self.search_engine.search(variation, num_results // 3)
                for result in results:
                    result["search_query"] = variation
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Search variation failed: {variation} - {str(e)}")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results[:num_results]
    
    async def _intelligent_analysis(self, search_results: List[Dict], depth: int) -> List[Dict[str, Any]]:
        """Intelligent content analysis using ZAI"""
        if depth < 2 or not search_results:
            return []
        
        detailed_analysis = []
        top_urls = [result["url"] for result in search_results[:10]]  # Top 10
        
        self.scraper = WebScraper()
        async with self.scraper:
            # Aggressive concurrent scraping
            semaphore = asyncio.Semaphore(15)  # High concurrency
            
            async def scrape_and_analyze(url):
                async with semaphore:
                    try:
                        scrape_result = await self.scraper.fetch_page(url)
                        if isinstance(scrape_result, dict) and "error" not in scrape_result:
                            # Use ZAI for content analysis
                            analysis = await self._analyze_content_with_zai(scrape_result)
                            return {
                                "url": url,
                                "title": scrape_result.get("title", ""),
                                "zai_analysis": analysis,
                                "content_length": len(scrape_result.get("content", "")),
                                "text_sample": scrape_result.get("text", "")[:500]
                            }
                    except Exception as e:
                        logger.warning(f"Analysis failed for {url}: {str(e)}")
                        return {"url": url, "error": str(e)}
            
            # Process all URLs concurrently
            tasks = [scrape_and_analyze(url) for url in top_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict):
                    detailed_analysis.append(result)
        
        return detailed_analysis
    
    async def _analyze_content_with_zai(self, content: Dict[str, Any]) -> str:
        """Analyze content using ZAI"""
        if not self.zai_client:
            return "Analysis unavailable"
        
        try:
            text = content.get("text", "")[:1500]  # Limit for ZAI
            title = content.get("title", "")
            
            prompt = f"""Title: {title}
Content: {text}

Provide 3 key insights in bullet points."""
            
            return await self.zai_client.generate_text(prompt, temperature=0.3)
        except Exception as e:
            logger.warning(f"Content analysis failed: {str(e)}")
            return "Analysis failed"
    
    async def _synthesize_with_zai(self, query: str, search_results: List[Dict], 
                                detailed_analysis: List[Dict]) -> Dict[str, Any]:
        """Synthesize research findings using ZAI"""
        if not self.zai_client:
            return {
                "summary": f"Research on '{query}' completed with {len(search_results)} sources.",
                "key_themes": [],
                "research_quality": "medium"
            }
        
        try:
            # Prepare synthesis input
            sources_summary = "\n".join([
                f"- {result.get('title', 'No title')}: {result.get('snippet', 'No snippet')[:100]}"
                for result in search_results[:10]
            ])
            
            analysis_summary = "\n".join([
                f"- {analysis.get('title', 'No title')}: {analysis.get('zai_analysis', 'No analysis')[:100]}"
                for analysis in detailed_analysis[:5]
            ])
            
            prompt = f"""Research Query: {query}

Sources:
{sources_summary}

Analysis:
{analysis_summary}

Synthesize into:
1. 2-sentence summary
2. 3 key themes
3. Quality assessment (high/medium/low)"""
            
            synthesis = await self.zai_client.generate_text(prompt, temperature=0.2)
            
            # Parse synthesis
            if synthesis:
                return {
                    "summary": synthesis,
                    "key_themes": self._extract_themes(synthesis),
                    "research_quality": self._assess_quality(synthesis),
                    "synthesis_length": len(synthesis)
                }
            
        except Exception as e:
            logger.warning(f"Synthesis failed: {str(e)}")
        
        return {
            "summary": f"Research on '{query}' completed with {len(search_results)} sources.",
            "key_themes": [],
            "research_quality": "medium"
        }
    
    def _extract_themes(self, synthesis: str) -> List[str]:
        """Extract themes from synthesis"""
        # Simple extraction - look for numbered lists or bullet points
        lines = synthesis.split('\n')
        themes = []
        
        for line in lines:
            if any(marker in line for marker in ['1.', '2.', '3.', '-', '•']):
                theme = line.strip()
                # Remove markers
                for marker in ['1.', '2.', '3.', '-', '•']:
                    theme = theme.replace(marker, '').strip()
                if theme and len(theme) > 3:
                    themes.append(theme)
        
        return themes[:3]  # Return top 3
    
    def _assess_quality(self, synthesis: str) -> str:
        """Assess research quality"""
        if len(synthesis) > 500:
            return "high"
        elif len(synthesis) > 200:
            return "medium"
        else:
            return "low"
    
    async def search_web(self, query: str, num_results: int = 20) -> List[Dict[str, Any]]:
        """Search the web for information"""
        if not self.search_engine:
            self.search_engine = SearchEngine()
        
        return await self.search_engine.search(query, num_results)
    
    async def analyze_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze web page content"""
        text = content.get("text", "")
        title = content.get("title", "")
        
        # Quick analysis
        word_count = len(text.split()) if text else 0
        
        return {
            "title": title,
            "word_count": word_count,
            "content_length": len(text),
            "has_structured_data": "metadata" in content
        }
    
    async def summarize_content(self, content: str, max_length: int = 200) -> str:
        """Summarize content"""
        if not self.zai_client:
            return content[:max_length] + "..." if len(content) > max_length else content
        
        try:
            return await self.zai_client.summarize_content(content, max_length)
        except Exception as e:
            logger.warning(f"Summarization failed: {str(e)}")
            return content[:max_length] + "..." if len(content) > max_length else content
    
    async def terminate(self):
        """Terminate the agent and cleanup resources"""
        if self.scraper:
            await self.scraper.__aexit__(None, None, None)
        await super().terminate()