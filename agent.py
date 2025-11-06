from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import uuid
import json
from loguru import logger

from .zai_integration import get_zai_client, with_zai_cache
from ..config import settings

class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    COMPLETED = "completed"
    TERMINATED = "terminated"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0

@dataclass
class AgentMessage:
    sender: str
    receiver: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

class BaseAgent(ABC):
    def __init__(self, agent_id: str = None, name: str = None):
        self.id = agent_id or str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.status = AgentStatus.IDLE
        self.current_task: Optional[Task] = None
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.knowledge_base: Dict[str, Any] = {}
        self.tools: Dict[str, Callable] = {}
        self.created_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.performance_metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "average_task_time": 0.0
        }
        
        # ZAI integration
        self.zai_client = get_zai_client()
        self.reasoning_cache = {}
        
        # Initialize tools
        self._initialize_tools()
        
    @abstractmethod
    async def process_task(self, task: Task) -> Any:
        """Process a single task and return the result"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        pass
    
    def _initialize_tools(self):
        """Initialize agent-specific tools"""
        pass
    
    async def assign_task(self, task: Task) -> bool:
        """Assign a task to this agent"""
        if self.status != AgentStatus.IDLE:
            return False
            
        self.current_task = task
        self.status = AgentStatus.BUSY
        task.assigned_to = self.id
        task.status = "in_progress"
        
        logger.info(f"Agent {self.name} assigned task: {task.description}")
        return True
    
    async def execute_task(self) -> Any:
        """Execute the currently assigned task"""
        if not self.current_task:
            raise ValueError("No task assigned")
            
        start_time = datetime.now()
        
        try:
            logger.info(f"Agent {self.name} executing task: {self.current_task.description}")
            
            # Pre-execution reasoning with ZAI
            await self._pre_execution_reasoning()
            
            # Execute the task
            result = await self.process_task(self.current_task)
            
            # Post-execution analysis with ZAI
            await self._post_execution_analysis(result)
            
            # Update task and agent status
            self.current_task.result = result
            self.current_task.status = "completed"
            self.current_task.progress = 100.0
            
            # Update performance metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["tasks_completed"] += 1
            self.performance_metrics["total_execution_time"] += execution_time
            self.performance_metrics["average_task_time"] = (
                self.performance_metrics["total_execution_time"] / 
                self.performance_metrics["tasks_completed"]
            )
            
            self.status = AgentStatus.COMPLETED
            logger.info(f"Agent {self.name} completed task successfully")
            
            return result
            
        except Exception as e:
            # Handle task failure
            self.current_task.error = str(e)
            self.current_task.status = "failed"
            self.status = AgentStatus.ERROR
            self.performance_metrics["tasks_failed"] += 1
            
            logger.error(f"Agent {self.name} failed task: {str(e)}")
            raise e
    
    @with_zai_cache
    async def _pre_execution_reasoning(self):
        """Optimized pre-execution reasoning using ZAI"""
        if not self.current_task or not self.zai_client:
            return
        
        # Concise reasoning prompt (< 200 tokens)
        prompt = f"""Agent: {self.name}
Task: {self.current_task.description}
Capabilities: {', '.join(self.get_capabilities())}

Plan approach in 2-3 bullet points."""
        
        try:
            reasoning = await self.zai_client.analyze_reasoning(
                self.current_task.description,
                f"Agent: {self.name}, Capabilities: {', '.join(self.get_capabilities())}"
            )
            if reasoning:
                self.knowledge_base["execution_plan"] = reasoning
        except Exception as e:
            logger.warning(f"Pre-execution reasoning failed: {str(e)}")
    
    @with_zai_cache
    async def _post_execution_analysis(self, result: Any):
        """Optimized post-execution analysis using ZAI"""
        if not self.current_task or not self.zai_client:
            return
        
        # Concise analysis prompt (< 200 tokens)
        prompt = f"""Task completed: {self.current_task.description}
Result summary needed in 1-2 sentences."""
        
        try:
            analysis = await self.zai_client.summarize_content(
                str(result)[:500],  # Limit input
                100  # Limit output
            )
            if analysis:
                self.knowledge_base["result_analysis"] = analysis
        except Exception as e:
            logger.warning(f"Post-execution analysis failed: {str(e)}")
    
    async def decompose_task(self, task: str) -> List[str]:
        """Optimized task decomposition using ZAI"""
        if not self.zai_client:
            return [task]  # Fallback
        
        try:
            subtasks = await self.zai_client.decompose_task(task)
            return subtasks or [task]
        except Exception as e:
            logger.warning(f"Task decomposition failed: {str(e)}")
            return [task]
    
    async def generate_insights(self, data: Any) -> str:
        """Generate insights using ZAI"""
        if not self.zai_client:
            return "Insights generation unavailable"
        
        try:
            prompt = f"""Analyze this data and provide 2-3 key insights:
{str(data)[:800]}"""
            
            return await self.zai_client.generate_text(prompt, temperature=0.3)
        except Exception as e:
            logger.warning(f"Insight generation failed: {str(e)}")
            return "Unable to generate insights"
    
    async def optimize_approach(self, task: str, current_approach: str) -> str:
        """Optimize approach using ZAI"""
        if not self.zai_client:
            return current_approach
        
        try:
            prompt = f"""Task: {task}
Current approach: {current_approach[:200]}

Suggest 1-2 improvements in 50 words."""
            
            return await self.zai_client.generate_text(prompt, temperature=0.2)
        except Exception as e:
            logger.warning(f"Approach optimization failed: {str(e)}")
            return current_approach
    
    async def send_message(self, receiver: str, message_type: str, content: Dict[str, Any]):
        """Send a message to another agent"""
        message = AgentMessage(
            sender=self.id,
            receiver=receiver,
            message_type=message_type,
            content=content
        )
        logger.info(f"Message sent from {self.name} to {receiver}: {message_type}")
    
    async def receive_message(self, message: AgentMessage):
        """Receive a message from another agent"""
        await self.message_queue.put(message)
    
    async def process_messages(self):
        """Process incoming messages"""
        while not self.message_queue.empty():
            message = await self.message_queue.get()
            await self._handle_message(message)
    
    async def _handle_message(self, message: AgentMessage):
        """Handle incoming message"""
        logger.info(f"Agent {self.name} received message: {message.message_type}")
    
    def update_heartbeat(self):
        """Update the agent's heartbeat timestamp"""
        self.last_heartbeat = datetime.now()
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "current_task": self.current_task.id if self.current_task else None,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "performance_metrics": self.performance_metrics,
            "capabilities": self.get_capabilities(),
            "zai_enabled": self.zai_client.client is not None if self.zai_client else False
        }
    
    async def terminate(self):
        """Terminate the agent"""
        self.status = AgentStatus.TERMINATED
        logger.info(f"Agent {self.name} terminated")
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, name={self.name}, status={self.status.value})>"