"""integration_snippets.py

Practical integration guide to tie all core systems together for a flagship SwarmForge deployment.
- Instantiates agents from EnhancedAgentFactory
- Attaches contextual memory
- Registers on agent event bus
- Demonstrates inter-agent task chaining and memory sharing
"""

import asyncio
from core.agent_factory_enhanced import EnhancedAgentFactory
from core.collaboration_and_memory import AgentEventBus, ContextualMemoryObject

# Initialize Event Bus for all agents
event_bus = AgentEventBus()

# List flagship agent types (expand as needed)
AGENT_TYPES = [
    "orchestrator",
    "researcher",
    "coder",
    "scraper",
    "analyzer",
    "content_generator",
    "searcher"
]

# Instantiate all flagship agents w/personality + memory + event capabilities
AGENTS = {}
for agent_type in AGENT_TYPES:
    agent = EnhancedAgentFactory.create_agent(agent_type)
    if agent:
        AGENTS[agent_type] = agent
        # Attach contextual memory for perpetual/project-wide recall
        agent.memory = ContextualMemoryObject(agent.id)
        # Register on event bus for messaging
        event_bus.register_agent(agent.id)

# Example: Full-circle flagship agent workflow
async def flagship_workflow(project_query: str):
    # Orchestrator starts by planning
    orchestrator = AGENTS["orchestrator"]
    plan = await orchestrator.communicate(f"Start flagship project: {project_query}")
    orchestrator.memory.remember({"step": "plan", "query": project_query, "plan": plan}, importance=1.0)

    # Pass plan to researcher
    researcher = AGENTS["researcher"]
    researcher.memory.share_with(orchestrator.memory)
    research_results = await researcher.communicate(f"Research for: {project_query}")
    researcher.memory.remember({"step": "research", "query": project_query, "results": research_results}, importance=0.9)

    # Coder receives research context
    coder = AGENTS["coder"]
    researcher.memory.share_with(coder.memory)
    code_result = await coder.communicate(f"Build based on research for: {project_query}")
    coder.memory.remember({"step": "code", "project": project_query, "result": code_result}, importance=0.8)

    # Scraper fetches additional data
    scraper = AGENTS["scraper"]
    coder.memory.share_with(scraper.memory)
    scrape_result = await scraper.communicate(f"Scrape additional product info for: {project_query}")
    scraper.memory.remember({"step": "scrape", "project": project_query, "result": scrape_result}, importance=0.8)

    # Analyzer interprets all collected data
    analyzer = AGENTS["analyzer"]
    scraper.memory.share_with(analyzer.memory)
    analysis_result = await analyzer.communicate(f"Analyze flagship data for: {project_query}")
    analyzer.memory.remember({"step": "analysis", "project": project_query, "result": analysis_result}, importance=0.8)

    # Content generator summarizes outputs
    content_gen = AGENTS["content_generator"]
    analyzer.memory.share_with(content_gen.memory)
    content = await content_gen.communicate(f"Generate flagship report for: {project_query}")
    content_gen.memory.remember({"step": "content", "project": project_query, "result": content}, importance=0.9)

    # Searcher links report to latest trends
    searcher = AGENTS["searcher"]
    content_gen.memory.share_with(searcher.memory)
    search_results = await searcher.communicate(f"Index flagship report for: {project_query}")
    searcher.memory.remember({"step": "search", "project": project_query, "result": search_results}, importance=0.7)

    # Final: Share context/project state to all agents
done_context = {"flagship_project": project_query, "status": "complete"}
    for agent in AGENTS.values():
        agent.memory.remember(done_context, importance=1.0)

    print("Flagship project full-circle workflow completed!")
    return {t: AGENTS[t].memory.recall(long_term=True) for t in AGENT_TYPES}

# Usage example:
# asyncio.run(flagship_workflow("NextGen AI Product Launch"))
