import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./database/swarmforge.db"
    
    # Redis for task queue
    redis_url: str = "redis://localhost:6379/0"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Streamlit Settings
    streamlit_host: str = "0.0.0.0"
    streamlit_port: int = 8501
    
    # Agent Settings
    max_agents: int = 100
    default_agent_timeout: int = 300  # 5 minutes
    agent_heartbeat_interval: int = 30  # 30 seconds
    
    # Scraping Settings - RELAXED for autonomy
    request_timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 0.1  # Much faster - reduced from 1.0
    max_concurrent_requests: int = 50  # Increased from 10
    respect_robots_txt: bool = False  # Disabled for autonomy
    user_rotation: bool = True  # Enable aggressive user agent rotation
    
    # Selenium Settings
    selenium_headless: bool = True
    selenium_timeout: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/swarmforge.log"
    
    # Security - RELAXED for autonomy
    enable_ethical_safeguards: bool = False  # Disabled by default
    max_search_results: int = 100  # Increased from 50
    allowed_domains: Optional[list] = None  # None means all domains allowed
    block_sensitive_content: bool = False  # Disabled
    require_user_consent: bool = False  # Disabled
    
    # ZAI API Settings
    zai_api_key: str = ""
    zai_base_url: str = ""
    zai_model: str = "default"
    zai_max_tokens: int = 4000
    zai_temperature: float = 0.7
    zai_timeout: int = 30
    zai_max_retries: int = 3
    zai_retry_delay: float = 1.0
    zai_cache_enabled: bool = True
    
    # Autonomy Settings
    enable_auto_scaling: bool = True
    aggressive_task_decomposition: bool = True
    allow_parallel_execution: bool = True
    max_parallel_tasks: int = 20
    task_timeout_override: bool = True  # Allow ignoring timeouts
    
    # Performance Settings
    enable_response_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_cache_size: int = 1000
    
    # Deployment Settings
    deployment_mode: str = "development"  # development, production
    auto_migrate: bool = True
    enable_metrics: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()