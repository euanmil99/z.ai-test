"""Dynamic Model Configuration System

Automatically detects platform and configures appropriate models:
- Windows: Full-power models (8B-70B parameters) with GPU acceleration
- Android: Lightweight models (1.1B-3.8B parameters) optimized for mobile
- Fallback: API-based models for limited systems
"""

import platform
import os
import psutil
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

class ModelDeploymentConfig:
    """Dynamically configures models based on platform and resources"""
    
    def __init__(self):
        self.platform = self.detect_platform()
        self.available_memory = self.get_available_memory()
        self.has_gpu = self.detect_gpu()
        self.model_config = self.load_model_config()
        self.cache_dir = self.get_cache_dir()
        
        logger.info(f"Platform: {self.platform}")
        logger.info(f"Memory: {self.available_memory}GB")
        logger.info(f"GPU: {self.has_gpu}")
    
    @staticmethod
    def detect_platform() -> str:
        """Detect if running on Windows, Android, or other platform"""
        system = platform.system().lower()
        
        # Check for Android
        if 'ANDROID_ROOT' in os.environ or 'ANDROID_DATA' in os.environ:
            return 'android'
        elif system == 'windows':
            return 'windows'
        elif system == 'linux':
            # Check if Termux (Android Linux environment)
            prefix = os.environ.get('PREFIX', '')
            if 'com.termux' in prefix or '/data/data/com.termux' in prefix:
                return 'android'
            return 'linux'
        elif system == 'darwin':
            return 'macos'
        else:
            return 'unknown'
    
    @staticmethod
    def get_available_memory() -> int:
        """Get available system memory in GB"""
        try:
            return psutil.virtual_memory().available // (1024**3)
        except Exception as e:
            logger.warning(f"Could not detect memory: {e}")
            return 8  # Default assumption
    
    @staticmethod
    def detect_gpu() -> bool:
        """Detect if CUDA-capable GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def get_cache_dir(self) -> Path:
        """Get appropriate cache directory for models"""
        if self.platform == 'android':
            base = Path('/sdcard/SwarmForge')
        else:
            base = Path.home() / '.swarmforge'
        
        cache_dir = base / 'models' / self.platform
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def load_model_config(self) -> Dict[str, Any]:
        """Load appropriate model configuration based on platform and resources"""
        
        if self.platform == 'android':
            return self.get_android_config()
        elif self.platform == 'windows' and self.available_memory >= 16 and self.has_gpu:
            return self.get_windows_full_config()
        elif self.platform in ['windows', 'linux', 'macos'] and self.available_memory >= 8:
            return self.get_medium_config()
        else:
            return self.get_fallback_config()
    
    def get_windows_full_config(self) -> Dict[str, Any]:
        """Full-power models for Windows with GPU"""
        logger.info("Loading FULL model configuration (Windows GPU)")
        
        return {
            "orchestrator": {
                "model": "microsoft/Phi-3-medium-4k-instruct",
                "parameters": "14B",
                "context_window": 4096,
                "quantization": "4bit",
                "device": "cuda",
                "torch_dtype": "float16",
                "load_in_4bit": True
            },
            "researcher": {
                "model": "meta-llama/Meta-Llama-3-70B-Instruct",
                "parameters": "70B",
                "context_window": 8192,
                "quantization": "4bit",
                "device": "cuda",
                "torch_dtype": "float16",
                "load_in_4bit": True
            },
            "coder": {
                "model": "codellama/CodeLlama-34b-Instruct-hf",
                "parameters": "34B",
                "context_window": 16384,
                "quantization": "4bit",
                "device": "cuda",
                "torch_dtype": "float16",
                "load_in_4bit": True
            },
            "scraper": {
                "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "parameters": "47B",
                "context_window": 32768,
                "quantization": "4bit",
                "device": "cuda",
                "torch_dtype": "float16",
                "load_in_4bit": True
            },
            "analyzer": {
                "model": "meta-llama/Meta-Llama-3-70B-Instruct",
                "parameters": "70B",
                "context_window": 8192,
                "quantization": "4bit",
                "device": "cuda",
                "torch_dtype": "float16",
                "load_in_4bit": True
            },
            "content_generator": {
                "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "parameters": "47B",
                "context_window": 32768,
                "quantization": "4bit",
                "device": "cuda",
                "torch_dtype": "float16",
                "load_in_4bit": True
            },
            "searcher": {
                "model": "microsoft/Phi-3-mini-4k-instruct",
                "parameters": "3.8B",
                "context_window": 4096,
                "quantization": "4bit",
                "device": "cuda",
                "torch_dtype": "float16",
                "load_in_4bit": True
            }
        }
    
    def get_android_config(self) -> Dict[str, Any]:
        """Lightweight GGUF models for Android"""
        logger.info("Loading LIGHTWEIGHT model configuration (Android)")
        
        return {
            "orchestrator": {
                "model": "TheBloke/Phi-3-mini-4K-Instruct-GGUF",
                "model_file": "phi-3-mini-4k-instruct.Q4_K_M.gguf",
                "parameters": "3.8B",
                "context_window": 2048,
                "quantization": "4bit",
                "device": "cpu",
                "n_threads": 4,
                "format": "gguf"
            },
            "researcher": {
                "model": "TheBloke/gemma-2b-it-GGUF",
                "model_file": "gemma-2b-it.Q4_K_M.gguf",
                "parameters": "2B",
                "context_window": 2048,
                "quantization": "4bit",
                "device": "cpu",
                "n_threads": 4,
                "format": "gguf"
            },
            "coder": {
                "model": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "model_file": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                "parameters": "1.1B",
                "context_window": 2048,
                "quantization": "4bit",
                "device": "cpu",
                "n_threads": 4,
                "format": "gguf"
            },
            "scraper": {
                "model": "TheBloke/phi-2-GGUF",
                "model_file": "phi-2.Q4_K_M.gguf",
                "parameters": "2.7B",
                "context_window": 2048,
                "quantization": "4bit",
                "device": "cpu",
                "n_threads": 4,
                "format": "gguf"
            },
            "analyzer": {
                "model": "TheBloke/gemma-2b-it-GGUF",
                "model_file": "gemma-2b-it.Q4_K_M.gguf",
                "parameters": "2B",
                "context_window": 2048,
                "quantization": "4bit",
                "device": "cpu",
                "n_threads": 4,
                "format": "gguf"
            },
            "content_generator": {
                "model": "TheBloke/phi-2-GGUF",
                "model_file": "phi-2.Q4_K_M.gguf",
                "parameters": "2.7B",
                "context_window": 2048,
                "quantization": "4bit",
                "device": "cpu",
                "n_threads": 4,
                "format": "gguf"
            },
            "searcher": {
                "model": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "model_file": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                "parameters": "1.1B",
                "context_window": 2048,
                "quantization": "4bit",
                "device": "cpu",
                "n_threads": 4,
                "format": "gguf"
            }
        }
    
    def get_medium_config(self) -> Dict[str, Any]:
        """Medium-sized models for systems without GPU"""
        logger.info("Loading MEDIUM model configuration (CPU)")
        
        return {
            "orchestrator": {
                "model": "microsoft/Phi-3-mini-4k-instruct",
                "parameters": "3.8B",
                "context_window": 4096,
                "quantization": "4bit",
                "device": "cpu",
                "torch_dtype": "float32",
                "load_in_4bit": True
            },
            "researcher": {
                "model": "google/gemma-2b-it",
                "parameters": "2B",
                "context_window": 8192,
                "quantization": "4bit",
                "device": "cpu",
                "torch_dtype": "float32",
                "load_in_4bit": True
            },
            "coder": {
                "model": "microsoft/Phi-2",
                "parameters": "2.7B",
                "context_window": 2048,
                "quantization": "4bit",
                "device": "cpu",
                "torch_dtype": "float32",
                "load_in_4bit": True
            },
            "scraper": {
                "model": "microsoft/Phi-2",
                "parameters": "2.7B",
                "context_window": 2048,
                "quantization": "4bit",
                "device": "cpu",
                "torch_dtype": "float32",
                "load_in_4bit": True
            },
            "analyzer": {
                "model": "google/gemma-2b-it",
                "parameters": "2B",
                "context_window": 8192,
                "quantization": "4bit",
                "device": "cpu",
                "torch_dtype": "float32",
                "load_in_4bit": True
            },
            "content_generator": {
                "model": "microsoft/Phi-2",
                "parameters": "2.7B",
                "context_window": 2048,
                "quantization": "4bit",
                "device": "cpu",
                "torch_dtype": "float32",
                "load_in_4bit": True
            },
            "searcher": {
                "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                "parameters": "1.1B",
                "context_window": 2048,
                "quantization": "4bit",
                "device": "cpu",
                "torch_dtype": "float32",
                "load_in_4bit": True
            }
        }
    
    def get_fallback_config(self) -> Dict[str, Any]:
        """API-based fallback for very limited systems"""
        logger.warning("Using FALLBACK configuration (API-based)")
        
        return {
            "all_agents": {
                "provider": "zai_api",
                "model": "default",
                "api_key_required": True,
                "device": "cloud",
                "fallback": True
            }
        }
    
    def get_model_for_agent(self, agent_type: str) -> Dict[str, Any]:
        """Get model configuration for specific agent type"""
        if "all_agents" in self.model_config:
            # Fallback configuration
            return self.model_config["all_agents"]
        
        return self.model_config.get(agent_type, self.model_config.get("orchestrator"))
    
    def should_use_local_models(self) -> bool:
        """Check if system should use local models"""
        return "all_agents" not in self.model_config
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            "platform": self.platform,
            "memory_gb": self.available_memory,
            "has_gpu": self.has_gpu,
            "cache_dir": str(self.cache_dir),
            "using_local_models": self.should_use_local_models(),
            "config_type": "full" if self.platform == "windows" and self.has_gpu else 
                          ("android" if self.platform == "android" else "medium")
        }

# Global singleton instance
deployment_config = ModelDeploymentConfig()

# Convenience functions
def get_model_config(agent_type: str) -> Dict[str, Any]:
    """Get model configuration for agent type"""
    return deployment_config.get_model_for_agent(agent_type)

def get_platform() -> str:
    """Get current platform"""
    return deployment_config.platform

def is_android() -> bool:
    """Check if running on Android"""
    return deployment_config.platform == "android"

def is_windows() -> bool:
    """Check if running on Windows"""
    return deployment_config.platform == "windows"

def has_gpu() -> bool:
    """Check if GPU is available"""
    return deployment_config.has_gpu

def get_cache_dir() -> Path:
    """Get model cache directory"""
    return deployment_config.cache_dir
