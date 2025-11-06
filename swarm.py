from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import uuid
from loguru import logger
from ..config import settings
from .agent import BaseAgent, Task, AgentStatus, TaskPriority

class SwarmCoordinator:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.completed_tasks: Dict[str, Task] = {}
        self.active_tasks: Dict[str, Task] = {}
        self.agent_factory = AgentFactory()
        self.is_running = False
        self.max_agents = settings.max_agents
        self.scaling_threshold = 5  # Spawn new agents if queue > this
        self.idle_timeout = 300  # Terminate idle agents after 5 minutes
        
    async def start(self):
        """Start the swarm coordinator"""
        self.is_running = True
        logger.info("Swarm coordinator started")
        
        # Start background tasks
        asyncio.create_task(self._process_task_queue())
        asyncio.create_task(self._monitor_agents())
        asyncio.create_task(self._auto_scale())
        
    async def stop(self):
        """Stop the swarm coordinator"""
        self.is_running = False
        
        # Terminate all agents
        for agent in self.agents.values():
            await agent.terminate()
        
        logger.info("Swarm coordinator stopped")
    
    async def submit_task(self, task: Task) -> str:
        """Submit a task to the swarm"""
        await self.task_queue.put(task)
        self.active_tasks[task.id] = task
        logger.info(f"Task submitted: {task.description}")
        return task.id
    
    async def _process_task_queue(self):
        """Process tasks from the queue"""
        while self.is_running:
            try:
                # Get task from queue
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Find or create suitable agent
                agent = await self._get_suitable_agent(task)
                
                if agent:
                    # Assign task to agent
                    await agent.assign_task(task)
                    
                    # Execute task asynchronously
                    asyncio.create_task(self._execute_agent_task(agent, task))
                else:
                    # No suitable agent available, put task back in queue
                    await self.task_queue.put(task)
                    await asyncio.sleep(0.1)  # Brief delay before retry
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing task queue: {str(e)}")
    
    async def _get_suitable_agent(self, task: Task) -> Optional[BaseAgent]:
        """Find or create a suitable agent for the task"""
        # First, try to find an idle agent with suitable capabilities
        for agent in self.agents.values():
            if agent.status == AgentStatus.IDLE:
                # Check if agent can handle this type of task
                if await self._agent_can_handle_task(agent, task):
                    return agent
        
        # If no suitable agent found and we haven't reached max agents, create one
        if len(self.agents) < self.max_agents:
            agent = await self.agent_factory.create_agent_for_task(task)
            if agent:
                self.agents[agent.id] = agent
                logger.info(f"Created new agent: {agent.name}")
                return agent
        
        return None
    
    async def _agent_can_handle_task(self, agent: BaseAgent, task: Task) -> bool:
        """Check if an agent can handle a specific task"""
        # This is a simplified check - in practice, you'd have more sophisticated matching
        capabilities = agent.get_capabilities()
        
        # Simple keyword matching for now
        task_desc = task.description.lower()
        for capability in capabilities:
            if capability.lower() in task_desc:
                return True
        
        return False
    
    async def _execute_agent_task(self, agent: BaseAgent, task: Task):
        """Execute a task on an agent"""
        try:
            result = await agent.execute_task()
            
            # Move task to completed
            task.result = result
            self.completed_tasks[task.id] = task
            self.active_tasks.pop(task.id, None)
            
            logger.info(f"Task completed: {task.description}")
            
        except Exception as e:
            logger.error(f"Task failed: {task.description} - {str(e)}")
            task.error = str(e)
            self.completed_tasks[task.id] = task
            self.active_tasks.pop(task.id, None)
    
    async def _monitor_agents(self):
        """Monitor agent health and status"""
        while self.is_running:
            try:
                current_time = datetime.now()
                agents_to_remove = []
                
                for agent_id, agent in self.agents.items():
                    # Check for idle timeout
                    if (agent.status == AgentStatus.IDLE and 
                        current_time - agent.last_heartbeat > timedelta(seconds=self.idle_timeout)):
                        agents_to_remove.append(agent_id)
                
                # Remove idle agents
                for agent_id in agents_to_remove:
                    agent = self.agents[agent_id]
                    await agent.terminate()
                    del self.agents[agent_id]
                    logger.info(f"Removed idle agent: {agent.name}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring agents: {str(e)}")
    
    async def _auto_scale(self):
        """Automatically scale the swarm based on demand"""
        while self.is_running:
            try:
                queue_size = self.task_queue.qsize()
                active_agents = sum(1 for agent in self.agents.values() if agent.status == AgentStatus.BUSY)
                
                # Scale up if queue is getting large
                if queue_size > self.scaling_threshold and len(self.agents) < self.max_agents:
                    # Create additional agents
                    num_to_create = min(queue_size - self.scaling_threshold, 
                                      self.max_agents - len(self.agents))
                    
                    for _ in range(num_to_create):
                        agent = await self.agent_factory.create_generic_agent()
                        if agent:
                            self.agents[agent.id] = agent
                            logger.info(f"Auto-scaled up - created agent: {agent.name}")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in auto-scaling: {str(e)}")
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall swarm status"""
        return {
            "total_agents": len(self.agents),
            "active_agents": sum(1 for agent in self.agents.values() if agent.status == AgentStatus.BUSY),
            "idle_agents": sum(1 for agent in self.agents.values() if agent.status == AgentStatus.IDLE),
            "queue_size": self.task_queue.qsize(),
            "completed_tasks": len(self.completed_tasks),
            "active_tasks": len(self.active_tasks),
            "agents": {agent_id: agent.get_status() for agent_id, agent in self.agents.items()}
        }

class AgentFactory:
    def __init__(self):
        self.agent_types = {}
        self._register_agent_types()
    
    def _register_agent_types(self):
        """Register available agent types"""
        # Import agent classes here to avoid circular imports
        from ..agents.web_scraper import WebScraperAgent
        from ..agents.researcher import ResearchAgent
        from ..agents.coder import CodeExecutorAgent
        from ..agents.orchestrator import TaskOrchestratorAgent
        from ..agents.analyzer import DataAnalyzerAgent
        from ..agents.content_generator import ContentGeneratorAgent
        from ..agents.searcher import SearchAgent
        
        self.agent_types = {
            "web_scraper": WebScraperAgent,
            "researcher": ResearchAgent,
            "coder": CodeExecutorAgent,
            "orchestrator": TaskOrchestratorAgent,
            "analyzer": DataAnalyzerAgent,
            "content_generator": ContentGeneratorAgent,
            "searcher": SearchAgent
        }
    
    async def create_agent_for_task(self, task: Task) -> Optional[BaseAgent]:
        """Create an agent suitable for the given task"""
        task_desc = task.description.lower()
        
        # Determine agent type based on task description
        if any(keyword in task_desc for keyword in ["scrape", "crawl", "extract", "fetch"]):
            return self.agent_types["web_scraper"]()
        elif any(keyword in task_desc for keyword in ["research", "analyze", "investigate"]):
            return self.agent_types["researcher"]()
        elif any(keyword in task_desc for keyword in ["code", "program", "script", "develop"]):
            return self.agent_types["coder"]()
        elif any(keyword in task_desc for keyword in ["coordinate", "organize", "manage"]):
            return self.agent_types["orchestrator"]()
        elif any(keyword in task_desc for keyword in ["data", "statistics", "metrics"]):
            return self.agent_types["analyzer"]()
        elif any(keyword in task_desc for keyword in ["write", "create", "generate"]):
            return self.agent_types["content_generator"]()
        elif any(keyword in task_desc for keyword in ["search", "find", "lookup"]):
            return self.agent_types["searcher"]()
        else:
            # Default to a generic agent
            return self.create_generic_agent()
    
    async def create_generic_agent(self) -> BaseAgent:
        """Create a generic agent for miscellaneous tasks"""
        # Default to researcher agent as it's most versatile
        return self.agent_types["researcher"]()
    
    def register_agent_type(self, name: str, agent_class: type):
        """Register a new agent type"""
        self.agent_types[name] = agent_class
    
    def get_available_types(self) -> List[str]:
        """Get list of available agent types"""
        return list(self.agent_types.keys())