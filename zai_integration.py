import os
import asyncio
import time
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from functools import wraps
import json
from loguru import logger

try:
    import ZAI
except ImportError:
    logger.warning("z-ai-web-dev-sdk not installed. Install with: pip install z-ai-web-dev-sdk")
    ZAI = None

@dataclass
class ZAIConfig:
    api_key: str = ""
    base_url: str = ""
    model: str = "default"
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

class ZAIClient:
    """Optimized z.ai API client with caching and rate limit handling"""
    
    def __init__(self, config: Optional[ZAIConfig] = None):
        self.config = config or self._load_config()
        self.client = None
        self.cache = {}  # Simple in-memory cache
        self.rate_limit_reset = 0
        self.request_count = 0
        self.last_request_time = 0
        
        if ZAI and self.config.api_key:
            asyncio.create_task(self._initialize_client())
    
    def _load_config(self) -> ZAIConfig:
        """Load configuration from environment variables"""
        return ZAIConfig(
            api_key=os.getenv("ZAI_API_KEY", ""),
            base_url=os.getenv("ZAI_BASE_URL", ""),
            model=os.getenv("ZAI_MODEL", "default"),
            max_tokens=int(os.getenv("ZAI_MAX_TOKENS", "4000")),
            temperature=float(os.getenv("ZAI_TEMPERATURE", "0.7")),
            timeout=int(os.getenv("ZAI_TIMEOUT", "30")),
            max_retries=int(os.getenv("ZAI_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("ZAI_RETRY_DELAY", "1.0"))
        )
    
    async def _initialize_client(self):
        """Initialize the ZAI client"""
        try:
            self.client = await ZAI.create()
            logger.info("ZAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ZAI client: {str(e)}")
            self.client = None
    
    def _get_cache_key(self, messages: List[Dict], **kwargs) -> str:
        """Generate cache key for request"""
        content = json.dumps(messages, sort_keys=True) + str(sorted(kwargs.items()))
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if response is cached"""
        return cache_key in self.cache
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response"""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # Simple cache expiration (1 hour)
            if time.time() - cached_data["timestamp"] < 3600:
                return cached_data["response"]
            else:
                del self.cache[cache_key]
        return None
    
    def _cache_response(self, cache_key: str, response: Dict):
        """Cache response"""
        self.cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        # Limit cache size
        if len(self.cache) > 1000:
            # Remove oldest entries
            oldest_keys = sorted(
                self.cache.keys(),
                key=lambda k: self.cache[k]["timestamp"]
            )[:100]
            for key in oldest_keys:
                del self.cache[key]
    
    async def _rate_limit_check(self):
        """Check and handle rate limits"""
        current_time = time.time()
        
        # Simple rate limiting (max 10 requests per second)
        if current_time - self.last_request_time < 0.1:
            await asyncio.sleep(0.1)
        
        self.last_request_time = current_time
    
    async def _exponential_backoff(self, attempt: int):
        """Exponential backoff for retries"""
        delay = self.config.retry_delay * (2 ** attempt)
        logger.warning(f"Rate limited, waiting {delay:.2f}s (attempt {attempt + 1})")
        await asyncio.sleep(delay)
    
    async def chat_completion(self, messages: List[Dict], **kwargs) -> Optional[Dict]:
        """Optimized chat completion with caching and rate limit handling"""
        if not self.client:
            logger.error("ZAI client not initialized")
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(messages, **kwargs)
        if self._is_cached(cache_key):
            logger.debug("Using cached response")
            return self._get_cached_response(cache_key)
        
        # Rate limit check
        await self._rate_limit_check()
        
        # Merge with default parameters
        params = {
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        params.update(kwargs)
        
        # Retry logic with exponential backoff
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.chat.completions.create(**params)
                
                # Cache successful response
                response_dict = {
                    "choices": response.choices,
                    "usage": response.usage if hasattr(response, 'usage') else None
                }
                self._cache_response(cache_key, response_dict)
                
                self.request_count += 1
                return response_dict
                
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    logger.error(f"Failed after {self.config.max_retries} attempts: {str(e)}")
                    return None
                
                await self._exponential_backoff(attempt)
        
        return None
    
    async def generate_text(self, prompt: str, **kwargs) -> Optional[str]:
        """Generate text from prompt (optimized)"""
        messages = [{"role": "user", "content": prompt}]
        response = await self.chat_completion(messages, **kwargs)
        
        if response and response.get("choices"):
            return response["choices"][0]["message"]["content"]
        return None
    
    async def analyze_reasoning(self, task: str, context: str = "") -> Optional[str]:
        """Optimized reasoning analysis"""
        prompt = f"""Task: {task}
Context: {context}

Provide concise analysis and action plan."""
        
        return await self.generate_text(prompt, temperature=0.3)
    
    async def decompose_task(self, task: str) -> Optional[List[str]]:
        """Optimized task decomposition"""
        prompt = f"""Break this task into 3-5 specific subtasks:
{task}

Return only the subtasks, one per line."""
        
        response = await self.generate_text(prompt, temperature=0.2)
        if response:
            return [line.strip() for line in response.split('\n') if line.strip()]
        return []
    
    async def generate_code(self, requirement: str, language: str = "python") -> Optional[str]:
        """Optimized code generation"""
        prompt = f"""Generate {language} code for:
{requirement}

Provide only the code, no explanations."""
        
        return await self.generate_text(prompt, temperature=0.1)
    
    async def summarize_content(self, content: str, max_length: int = 200) -> Optional[str]:
        """Optimized content summarization"""
        prompt = f"""Summarize in {max_length} chars:
{content[:2000]}"""
        
        return await self.generate_text(prompt, temperature=0.3)
    
    async def extract_information(self, text: str, info_type: str) -> Optional[str]:
        """Optimized information extraction"""
        prompt = f"""Extract {info_type} from:
{text[:1000]}

Provide only the extracted information."""
        
        return await self.generate_text(prompt, temperature=0.1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "requests_made": self.request_count,
            "cache_size": len(self.cache),
            "client_initialized": self.client is not None,
            "config": {
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
        }

# Global client instance
_zai_client = None

def get_zai_client() -> ZAIClient:
    """Get global ZAI client instance"""
    global _zai_client
    if _zai_client is None:
        _zai_client = ZAIClient()
    return _zai_client

def with_zai_cache(func):
    """Decorator to cache function results"""
    cache = {}
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        cache_key = str(args) + str(sorted(kwargs.items()))
        
        if cache_key in cache:
            return cache[cache_key]
        
        result = await func(*args, **kwargs)
        cache[cache_key] = result
        
        # Limit cache size
        if len(cache) > 100:
            oldest_keys = list(cache.keys())[:50]
            for key in oldest_keys:
                del cache[key]
        
        return result
    
    return wrapper