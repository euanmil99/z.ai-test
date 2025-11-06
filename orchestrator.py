from typing import List, Dict, Any
from ..core import BaseAgent, Task, TaskPriority
from loguru import logger
import asyncio

class TaskOrchestratorAgent(BaseAgent):
    def __init__(self, agent_id: str = None, name: str = None):
        super().__init__(agent_id, name or "TaskOrchestratorAgent")
        self.subtasks_created = []
        self.task_dependencies = {}
    
    def get_capabilities(self) -> List[str]:
        return [
            "task_decomposition",
            "workflow_orchestration",
            "agent_coordination",
            "dependency_management",
            "task_prioritization",
            "resource_allocation",
            "progress_monitoring"
        ]
    
    def _initialize_tools(self):
        """Initialize orchestration tools"""
        self.tools = {
            "decompose_task": self.decompose_task,
            "create_workflow": self.create_workflow,
            "assign_priorities": self.assign_priorities,
            "monitor_progress": self.monitor_progress,
            "handle_dependencies": self.handle_dependencies
        }
    
    async def process_task(self, task: Task) -> Any:
        """Process task orchestration"""
        try:
            parameters = task.parameters
            complexity = parameters.get("complexity", "medium")
            max_subtasks = parameters.get("max_subtasks", 10)
            auto_execute = parameters.get("auto_execute", True)
            
            # Step 1: Decompose the main task
            subtasks = await self.decompose_task(task, max_subtasks)
            
            if not subtasks:
                # If no subtasks created, try to execute directly
                return await self.execute_simple_task(task)
            
            # Step 2: Create workflow and dependencies
            workflow = await self.create_workflow(subtasks)
            
            # Step 3: Assign priorities
            prioritized_tasks = await self.assign_priorities(workflow)
            
            # Step 4: Submit tasks to swarm (if auto_execute is enabled)
            submitted_tasks = []
            if auto_execute:
                # This would interact with the swarm coordinator
                # For now, we'll just return the orchestrated plan
                submitted_tasks = prioritized_tasks
            
            return {
                "orchestration_result": "success",
                "main_task": task.description,
                "subtasks_created": len(subtasks),
                "workflow_steps": len(workflow),
                "prioritized_tasks": prioritized_tasks,
                "execution_plan": self.generate_execution_plan(prioritized_tasks),
                "estimated_duration": self.estimate_duration(prioritized_tasks)
            }
            
        except Exception as e:
            logger.error(f"Task orchestration failed: {str(e)}")
            raise e
    
    async def decompose_task(self, task: Task, max_subtasks: int = 10) -> List[Task]:
        """Decompose a complex task into smaller subtasks"""
        description = task.description.lower()
        subtasks = []
        
        # Common decomposition patterns
        if any(keyword in description for keyword in ["research", "analyze", "investigate"]):
            subtasks.extend(await self._decompose_research_task(task))
        elif any(keyword in description for keyword in ["build", "create", "develop", "code"]):
            subtasks.extend(await self._decompose_development_task(task))
        elif any(keyword in description for keyword in ["scrape", "extract", "collect"]):
            subtasks.extend(await self._decompose_scraping_task(task))
        elif any(keyword in description for keyword in ["write", "generate", "content"]):
            subtasks.extend(await self._decompose_content_task(task))
        else:
            # Generic decomposition
            subtasks.extend(await self._decompose_generic_task(task))
        
        # Limit number of subtasks
        return subtasks[:max_subtasks]
    
    async def _decompose_research_task(self, task: Task) -> List[Task]:
        """Decompose research tasks"""
        subtasks = []
        
        # Search task
        search_task = Task(
            description=f"Search for information: {task.description}",
            priority=TaskPriority.HIGH,
            parameters={"query": task.description, "num_results": 10}
        )
        subtasks.append(search_task)
        
        # Analysis task
        analysis_task = Task(
            description=f"Analyze research findings for: {task.description}",
            priority=TaskPriority.MEDIUM,
            dependencies=[search_task.id],
            parameters={"depth": 2, "analyze_sources": True}
        )
        subtasks.append(analysis_task)
        
        # Summary task
        summary_task = Task(
            description=f"Summarize research on: {task.description}",
            priority=TaskPriority.MEDIUM,
            dependencies=[analysis_task.id],
            parameters={"max_length": 500}
        )
        subtasks.append(summary_task)
        
        return subtasks
    
    async def _decompose_development_task(self, task: Task) -> List[Task]:
        """Decompose development tasks"""
        subtasks = []
        
        # Requirements analysis
        requirements_task = Task(
            description=f"Analyze requirements for: {task.description}",
            priority=TaskPriority.HIGH,
            parameters={"analysis_type": "requirements"}
        )
        subtasks.append(requirements_task)
        
        # Design task
        design_task = Task(
            description=f"Design solution for: {task.description}",
            priority=TaskPriority.HIGH,
            dependencies=[requirements_task.id],
            parameters={"design_level": "high_level"}
        )
        subtasks.append(design_task)
        
        # Implementation task
        impl_task = Task(
            description=f"Implement: {task.description}",
            priority=TaskPriority.HIGH,
            dependencies=[design_task.id],
            parameters={"language": "python", "include_tests": True}
        )
        subtasks.append(impl_task)
        
        # Testing task
        test_task = Task(
            description=f"Test implementation of: {task.description}",
            priority=TaskPriority.MEDIUM,
            dependencies=[impl_task.id],
            parameters={"test_type": "automated"}
        )
        subtasks.append(test_task)
        
        return subtasks
    
    async def _decompose_scraping_task(self, task: Task) -> List[Task]:
        """Decompose web scraping tasks"""
        subtasks = []
        
        # Target identification
        target_task = Task(
            description=f"Identify scraping targets for: {task.description}",
            priority=TaskPriority.HIGH,
            parameters={"target_type": "websites"}
        )
        subtasks.append(target_task)
        
        # Scraping execution
        scrape_task = Task(
            description=f"Scrape data for: {task.description}",
            priority=TaskPriority.HIGH,
            dependencies=[target_task.id],
            parameters={"use_selenium": False, "extract_links": True}
        )
        subtasks.append(scrape_task)
        
        # Data processing
        process_task = Task(
            description=f"Process scraped data for: {task.description}",
            priority=TaskPriority.MEDIUM,
            dependencies=[scrape_task.id],
            parameters={"processing_type": "cleaning_and_structuring"}
        )
        subtasks.append(process_task)
        
        return subtasks
    
    async def _decompose_content_task(self, task: Task) -> List[Task]:
        """Decompose content generation tasks"""
        subtasks = []
        
        # Research for content
        research_task = Task(
            description=f"Research content for: {task.description}",
            priority=TaskPriority.HIGH,
            parameters={"content_research": True}
        )
        subtasks.append(research_task)
        
        # Content generation
        generate_task = Task(
            description=f"Generate content: {task.description}",
            priority=TaskPriority.HIGH,
            dependencies=[research_task.id],
            parameters={"content_type": "article", "word_count": 1000}
        )
        subtasks.append(generate_task)
        
        # Content review
        review_task = Task(
            description=f"Review and refine content: {task.description}",
            priority=TaskPriority.MEDIUM,
            dependencies=[generate_task.id],
            parameters={"review_type": "quality_check"}
        )
        subtasks.append(review_task)
        
        return subtasks
    
    async def _decompose_generic_task(self, task: Task) -> List[Task]:
        """Decompose generic tasks"""
        subtasks = []
        
        # Analysis
        analysis_task = Task(
            description=f"Analyze task: {task.description}",
            priority=TaskPriority.HIGH,
            parameters={"analysis_depth": "medium"}
        )
        subtasks.append(analysis_task)
        
        # Execution
        execute_task = Task(
            description=f"Execute task: {task.description}",
            priority=TaskPriority.HIGH,
            dependencies=[analysis_task.id],
            parameters={}
        )
        subtasks.append(execute_task)
        
        # Validation
        validate_task = Task(
            description=f"Validate results: {task.description}",
            priority=TaskPriority.MEDIUM,
            dependencies=[execute_task.id],
            parameters={"validation_type": "quality_check"}
        )
        subtasks.append(validate_task)
        
        return subtasks
    
    async def create_workflow(self, subtasks: List[Task]) -> List[Task]:
        """Create a workflow from subtasks"""
        # Sort tasks by dependencies
        workflow = []
        processed = set()
        
        def add_task(task):
            if task.id in processed:
                return
            
            # Add dependencies first
            for dep_id in task.dependencies:
                dep_task = next((t for t in subtasks if t.id == dep_id), None)
                if dep_task:
                    add_task(dep_task)
            
            workflow.append(task)
            processed.add(task.id)
        
        for task in subtasks:
            add_task(task)
        
        return workflow
    
    async def assign_priorities(self, workflow: List[Task]) -> List[Task]:
        """Assign priorities to workflow tasks"""
        # Simple priority assignment based on task type and position
        for i, task in enumerate(workflow):
            if task.priority == TaskPriority.MEDIUM:  # Only modify if not explicitly set
                # Earlier tasks get higher priority
                if i < len(workflow) // 3:
                    task.priority = TaskPriority.HIGH
                elif i > 2 * len(workflow) // 3:
                    task.priority = TaskPriority.LOW
                # Others remain MEDIUM
        
        # Sort by priority and dependencies
        prioritized = sorted(workflow, key=lambda t: (
            -t.priority.value,  # Higher priority first
            len(t.dependencies)  # Fewer dependencies first
        ))
        
        return prioritized
    
    def generate_execution_plan(self, tasks: List[Task]) -> Dict[str, Any]:
        """Generate an execution plan for the tasks"""
        plan = {
            "total_tasks": len(tasks),
            "phases": [],
            "parallel_tasks": [],
            "critical_path": []
        }
        
        # Group tasks by dependency level
        levels = []
        remaining = tasks.copy()
        
        while remaining:
            current_level = []
            for task in remaining[:]:
                if all(dep not in [t.id for t in remaining] for dep in task.dependencies):
                    current_level.append(task)
                    remaining.remove(task)
            
            if current_level:
                levels.append(current_level)
            else:
                # Circular dependency or orphaned tasks
                levels.append(remaining)
                break
        
        plan["phases"] = [
            {
                "phase": i + 1,
                "tasks": [t.description for t in level],
                "can_run_parallel": len(level) > 1
            }
            for i, level in enumerate(levels)
        ]
        
        return plan
    
    def estimate_duration(self, tasks: List[Task]) -> Dict[str, Any]:
        """Estimate task execution duration"""
        # Simple estimation based on task type
        duration_map = {
            "search": 30,      # seconds
            "scrape": 60,
            "analyze": 120,
            "code": 180,
            "test": 90,
            "write": 150,
            "review": 60
        }
        
        total_seconds = 0
        for task in tasks:
            # Estimate based on keywords in description
            estimated = 60  # default 1 minute
            desc = task.description.lower()
            
            for keyword, duration in duration_map.items():
                if keyword in desc:
                    estimated = duration
                    break
            
            total_seconds += estimated
        
        return {
            "estimated_seconds": total_seconds,
            "estimated_minutes": round(total_seconds / 60, 1),
            "estimated_hours": round(total_seconds / 3600, 2)
        }
    
    async def execute_simple_task(self, task: Task) -> Dict[str, Any]:
        """Execute a simple task without decomposition"""
        return {
            "orchestration_result": "simple_execution",
            "task": task.description,
            "message": "Task executed directly without decomposition",
            "execution_type": "single_agent"
        }
    
    async def monitor_progress(self, tasks: List[Task]) -> Dict[str, Any]:
        """Monitor progress of multiple tasks"""
        completed = sum(1 for t in tasks if t.status == "completed")
        failed = sum(1 for t in tasks if t.status == "failed")
        in_progress = sum(1 for t in tasks if t.status == "in_progress")
        pending = sum(1 for t in tasks if t.status == "pending")
        
        return {
            "total_tasks": len(tasks),
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": pending,
            "completion_rate": completed / len(tasks) if tasks else 0,
            "success_rate": completed / (completed + failed) if (completed + failed) > 0 else 0
        }