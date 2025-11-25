"""EnhancedAgentFactory for SwarmForge multi-agent army.
Creates agents with specific personalities and loads platform/model config dynamically."""

from typing import Optional, Dict, Any
from .agent_with_personality import PersonalityAgent
from ..config.model_config import deployment_config

class EnhancedAgentFactory:
    PERSONALITY_PROFILES = {
        "orchestrator": {
            "decision_making": "analytical_strategic",
            "communication": "formal_directive",
            "risk_tolerance": "low",
            "collaboration": "coordinator",
            "strength": "planning_and_orchestration",
            "weakness": "inflexible_with_creativity"
        },
        "researcher": {
            "decision_making": "evidence_based",
            "communication": "academic_formal",
            "risk_tolerance": "very_low",
            "collaboration": "contributor",
            "strength": "information_synthesis",
            "weakness": "slow_and_cautious"
        },
        "coder": {
            "decision_making": "logic_driven",
            "communication": "technical_concise",
            "risk_tolerance": "medium",
            "collaboration": "implementer",
            "strength": "code_generation_execution",
            "weakness": "overlooks_user_experience"
        },
        "scraper": {
            "decision_making": "opportunistic_aggressive",
            "communication": "direct_assertive",
            "risk_tolerance": "high",
            "collaboration": "independent_operator",
            "strength": "data_extraction_persistence",
            "weakness": "reckless_norm_violation"
        },
        "analyzer": {
            "decision_making": "statistical_empirical",
            "communication": "analytical_questioning",
            "risk_tolerance": "low",
            "collaboration": "advisor",
            "strength": "pattern_recognition",
            "weakness": "paralyzed_by_incomplete_data"
        },
        "content_generator": {
            "decision_making": "creative_intuitive",
            "communication": "expressive_engaging",
            "risk_tolerance": "medium_high",
            "collaboration": "creator",
            "strength": "content_creation",
            "weakness": "sacrifices_accuracy_for_style"
        },
        "searcher": {
            "decision_making": "speed_optimized",
            "communication": "brief_efficient",
            "risk_tolerance": "medium",
            "collaboration": "information_provider",
            "strength": "rapid_retrieval",
            "weakness": "misses_nuanced_context"
        }
    }

    @classmethod
    def create_agent(cls, agent_type: str, **kwargs) -> Optional[PersonalityAgent]:
        personality = cls.PERSONALITY_PROFILES.get(agent_type)
        if not personality:
            return None

        # Import the agent classes as needed
        AGENT_CLASS_MAP = {
            "orchestrator": "TaskOrchestratorAgent",
            "researcher": "ResearchAgent",
            "coder": "CodeExecutorAgent",
            "scraper": "WebScraperAgent",
            "analyzer": "DataAnalyzerAgent",
            "content_generator": "ContentGeneratorAgent",
            "searcher": "SearchAgent"
        }
        agent_class_str = AGENT_CLASS_MAP.get(agent_type)
        if not agent_class_str:
            return None

        # Dynamically import so module doesn't have circular deps
        agent_module = __import__(f"..agents.{agent_type}", fromlist=[agent_class_str])
        AgentClass = getattr(agent_module, agent_class_str)
        agent = AgentClass(**kwargs)

        # Enhance with personality and model awareness
        agent = PersonalityAgent(agent_id=agent.id, name=agent.name, personality=personality)
        agent.model_config = deployment_config.model_config.get(agent_type)
        return agent
