from typing import List, Dict, Any
from ..core import BaseAgent, Task
from ..tools import SearchEngine
from loguru import logger
import asyncio

class SearchAgent(BaseAgent):
    def __init__(self, agent_id: str = None, name: str = None):
        super().__init__(agent_id, name or "SearchAgent")
        self.search_engine = None
    
    def get_capabilities(self) -> List[str]:
        return [
            "web_search",
            "information_retrieval",
            "source_validation",
            "result_ranking",
            "query_optimization",
            "deep_search",
            "fact_finding"
        ]
    
    def _initialize_tools(self):
        """Initialize search tools"""
        self.tools = {
            "search_web": self.search_web,
            "deep_search": self.perform_deep_search,
            "validate_sources": self.validate_sources,
            "rank_results": self.rank_results,
            "optimize_query": self.optimize_query
        }
    
    async def process_task(self, task: Task) -> Any:
        """Process search task"""
        try:
            if not self.search_engine:
                self.search_engine = SearchEngine()
            
            parameters = task.parameters
            query = parameters.get("query", task.description)
            num_results = parameters.get("num_results", 10)
            search_type = parameters.get("search_type", "basic")
            validate = parameters.get("validate_sources", True)
            deep_search = parameters.get("deep_search", False)
            
            # Perform search based on type
            if search_type == "deep" or deep_search:
                results = await self.perform_deep_search(query, num_results)
            else:
                results = await self.search_web(query, num_results)
            
            if not results:
                return {"error": "No search results found", "query": query}
            
            # Validate sources if requested
            if validate:
                validated_results = await self.validate_sources(results)
            else:
                validated_results = results
            
            # Rank results
            ranked_results = await self.rank_results(validated_results, query)
            
            return {
                "query": query,
                "search_type": search_type,
                "results_count": len(ranked_results),
                "results": ranked_results,
                "search_metadata": {
                    "validation_performed": validate,
                    "ranking_performed": True,
                    "deep_search_performed": deep_search
                }
            }
            
        except Exception as e:
            logger.error(f"Search task failed: {str(e)}")
            raise e
    
    async def search_web(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Perform basic web search"""
        if not self.search_engine:
            self.search_engine = SearchEngine()
        
        results = await self.search_engine.search(query, num_results)
        
        # Enhance results with additional metadata
        enhanced_results = []
        for i, result in enumerate(results):
            enhanced_result = {
                **result,
                "search_rank": i + 1,
                "relevance_score": self._calculate_relevance(result, query),
                "domain_authority": self._estimate_domain_authority(result.get("url", "")),
                "content_type": self._detect_content_type(result),
                "freshness": self._estimate_freshness(result)
            }
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
    
    async def perform_deep_search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Perform deep search with multiple query variations"""
        
        # Generate query variations
        query_variations = await self._generate_query_variations(query)
        
        all_results = []
        
        # Search with each variation
        for variation in query_variations:
            try:
                variation_results = await self.search_web(variation, num_results // len(query_variations))
                
                # Mark which query generated these results
                for result in variation_results:
                    result["query_variation"] = variation
                
                all_results.extend(variation_results)
                
            except Exception as e:
                logger.warning(f"Deep search variation failed: {variation} - {str(e)}")
                continue
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        
        for result in all_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        # Sort by relevance and return top results
        unique_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return unique_results[:num_results]
    
    async def validate_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and score sources"""
        
        validated_results = []
        
        for result in results:
            url = result.get("url", "")
            domain = self._extract_domain(url)
            
            validation_score = {
                "domain_reputation": self._check_domain_reputation(domain),
                "content_quality": self._assess_content_quality(result),
                "source_type": self._classify_source_type(domain),
                "bias_indicator": self._detect_potential_bias(result),
                "fact_check_history": self._check_fact_check_history(domain)
            }
            
            # Calculate overall validation score
            overall_score = sum(validation_score.values()) / len(validation_score)
            
            validated_result = {
                **result,
                "validation": {
                    **validation_score,
                    "overall_score": overall_score,
                    "trust_level": self._determine_trust_level(overall_score)
                }
            }
            
            validated_results.append(validated_result)
        
        return validated_results
    
    async def rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank search results by relevance and quality"""
        
        def calculate_ranking_score(result):
            score = 0
            
            # Base relevance score
            relevance = result.get("relevance_score", 0)
            score += relevance * 0.4
            
            # Validation score
            validation = result.get("validation", {})
            validation_score = validation.get("overall_score", 0.5)
            score += validation_score * 0.3
            
            # Domain authority
            domain_authority = result.get("domain_authority", 0.5)
            score += domain_authority * 0.2
            
            # Freshness
            freshness = result.get("freshness", 0.5)
            score += freshness * 0.1
            
            return score
        
        # Calculate ranking scores
        for result in results:
            result["ranking_score"] = calculate_ranking_score(result)
        
        # Sort by ranking score
        ranked_results = sorted(results, key=lambda x: x.get("ranking_score", 0), reverse=True)
        
        # Update ranks
        for i, result in enumerate(ranked_results):
            result["final_rank"] = i + 1
        
        return ranked_results
    
    async def optimize_query(self, query: str) -> str:
        """Optimize search query for better results"""
        
        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = query.lower().split()
        filtered_words = [word for word in words if word not in stop_words]
        
        # Add context-specific terms
        optimized_query = " ".join(filtered_words)
        
        # Add quotes for exact phrases if query is long enough
        if len(filtered_words) > 3:
            # Keep first 2 words as exact phrase
            exact_phrase = " ".join(filtered_words[:2])
            remaining = " ".join(filtered_words[2:])
            optimized_query = f'"{exact_phrase}" {remaining}'
        
        return optimized_query
    
    async def _generate_query_variations(self, query: str) -> List[str]:
        """Generate variations of the search query"""
        
        variations = [query]
        
        # Add common search operators
        variations.append(f"{query} tutorial")
        variations.append(f"{query} guide")
        variations.append(f"how to {query}")
        variations.append(f"{query} examples")
        variations.append(f"{query} best practices")
        
        # Add quotes for exact search
        if len(query.split()) > 1:
            variations.append(f'"{query}"')
        
        return variations[:6]  # Limit to 6 variations
    
    def _calculate_relevance(self, result: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for a result"""
        
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        query_lower = query.lower()
        query_words = query_lower.split()
        
        score = 0
        
        # Check for exact query match
        if query_lower in title:
            score += 0.5
        if query_lower in snippet:
            score += 0.3
        
        # Check for individual word matches
        title_word_matches = sum(1 for word in query_words if word in title)
        snippet_word_matches = sum(1 for word in query_words if word in snippet)
        
        score += (title_word_matches * 0.1) + (snippet_word_matches * 0.05)
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _estimate_domain_authority(self, url: str) -> float:
        """Estimate domain authority (simplified)"""
        
        domain = self._extract_domain(url)
        
        # High authority domains
        high_authority = [
            "wikipedia.org", "gov", "edu", "org",
            "reuters.com", "ap.org", "bbc.com", "cnn.com",
            "nature.com", "science.org", "ieee.org"
        ]
        
        # Medium authority domains
        medium_authority = [
            "medium.com", "github.com", "stackoverflow.com",
            "linkedin.com", "forbes.com", "techcrunch.com"
        ]
        
        if any(auth in domain for auth in high_authority):
            return 0.9
        elif any(auth in domain for auth in medium_authority):
            return 0.7
        else:
            return 0.5  # Default/unknown authority
    
    def _detect_content_type(self, result: Dict[str, Any]) -> str:
        """Detect the type of content"""
        
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        content = f"{title} {snippet}"
        
        if any(word in content for word in ["tutorial", "how to", "guide"]):
            return "tutorial"
        elif any(word in content for word in ["news", "breaking", "report"]):
            return "news"
        elif any(word in content for word in ["research", "study", "analysis"]):
            return "research"
        elif any(word in content for word in ["blog", "opinion", "thoughts"]):
            return "blog"
        elif any(word in content for word in ["docs", "documentation", "api"]):
            return "documentation"
        else:
            return "general"
    
    def _estimate_freshness(self, result: Dict[str, Any]) -> float:
        """Estimate content freshness (simplified)"""
        
        # In a real implementation, you'd parse actual dates
        # For now, return a default value
        return 0.7
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def _check_domain_reputation(self, domain: str) -> float:
        """Check domain reputation"""
        
        # Known good domains
        if any(good in domain for good in ["wikipedia", "gov", "edu", "reuters", "ap"]):
            return 0.9
        
        # Known problematic domains (simplified)
        if any(bad in domain for bad in ["spam", "fake", "hoax"]):
            return 0.2
        
        return 0.6  # Neutral
    
    def _assess_content_quality(self, result: Dict[str, Any]) -> float:
        """Assess content quality"""
        
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        
        # Quality indicators
        quality_score = 0.5  # Base score
        
        # Title length (not too short, not too long)
        if 10 <= len(title) <= 100:
            quality_score += 0.1
        
        # Snippet length
        if 50 <= len(snippet) <= 300:
            quality_score += 0.1
        
        # No clickbait indicators
        clickbait_words = ["shocking", "unbelievable", "you won't believe", "miracle"]
        if not any(word in title.lower() for word in clickbait_words):
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _classify_source_type(self, domain: str) -> str:
        """Classify the type of source"""
        
        if "gov" in domain:
            return "government"
        elif "edu" in domain:
            return "educational"
        elif "org" in domain:
            return "non_profit"
        elif any(news in domain for news in ["cnn", "bbc", "reuters", "ap"]):
            return "news"
        elif any(blog in domain for blog in ["blog", "medium", "substack"]):
            return "blog"
        else:
            return "commercial"
    
    def _detect_potential_bias(self, result: Dict[str, Any]) -> float:
        """Detect potential bias (0 = unbiased, 1 = highly biased)"""
        
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        content = f"{title} {snippet}"
        
        # Bias indicators (simplified)
        bias_indicators = [
            "shocking", "outrageous", "incredible", "unbelievable",
            "worst ever", "best ever", "only truth", "real story"
        ]
        
        bias_count = sum(1 for indicator in bias_indicators if indicator in content)
        
        return min(bias_count * 0.2, 1.0)
    
    def _check_fact_check_history(self, domain: str) -> float:
        """Check fact-checking history"""
        
        # In a real implementation, you'd check against fact-checking databases
        # For now, return a default based on domain type
        if any(good in domain for good in ["reuters", "ap", "bbc"]):
            return 0.9
        elif any(questionable in domain for questionable in ["fake", "hoax"]):
            return 0.2
        else:
            return 0.6
    
    def _determine_trust_level(self, score: float) -> str:
        """Determine trust level based on score"""
        
        if score >= 0.8:
            return "highly_trusted"
        elif score >= 0.6:
            return "trusted"
        elif score >= 0.4:
            return "moderately_trusted"
        else:
            return "low_trust"