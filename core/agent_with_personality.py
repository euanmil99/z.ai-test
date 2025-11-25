"""PersonalityAgent: Enhanced BaseAgent with Personality and Model Awareness
"""

from typing import Dict, Any, List
from ..config.model_config import deployment_config
from .agent import BaseAgent, Task
import random
import asyncio

class PersonalityAgent(BaseAgent):
    """Enhanced agent with distinct personality traits and model awareness"""
    def __init__(self, agent_id: str = None, name: str = None, personality: Dict[str, Any] = None):
        super().__init__(agent_id, name)
        self.personality = personality or self.get_default_personality()
        self.model_config = self.load_agent_model()
        self.communication_style = self.personality.get("communication", "neutral")

    def get_default_personality(self) -> Dict[str, Any]:
        return {
            "decision_making": "balanced",
            "communication": "neutral",
            "risk_tolerance": "medium",
            "collaboration": "team_player",
            "strength": "versatility",
            "weakness": "none_specific"
        }

    def load_agent_model(self) -> Dict[str, Any]:
        agent_type = self.__class__.__name__.replace("Agent", "").lower()
        config = deployment_config.model_config.get(agent_type, deployment_config.model_config.get("orchestrator"))
        return config

    async def communicate(self, message: str, target: str = "user") -> str:
        style = self.communication_style
        if style == "formal_directive":
            prefix = random.choice(["Directive:", "Action Required:", "Task Assignment:"])
            return f"{prefix} {message}"
        elif style == "academic_formal":
            prefix = random.choice(["Research indicates:", "Analysis shows:", "Evidence suggests:"])
            return f"{prefix} {message}"
        elif style == "technical_concise":
            return f"[{self.name}] {message}"
        elif style == "direct_assertive":
            prefix = random.choice(["Target acquired:", "Extracting:", "Capturing:"])
            return f"{prefix} {message}"
        elif style == "analytical_questioning":
            suffix = random.choice([" - requires validation", " - confidence level: high", " - statistical significance noted"])
            return f"{message}{suffix}"
        elif style == "expressive_engaging":
            prefix = random.choice(["Creating:", "Crafting:", "Generating:"])
            return f"{prefix} {message} ✨"
        elif style == "brief_efficient":
            return f"→ {message}"
        else:
            return message

    async def make_decision(self, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        decision_style = self.personality.get("decision_making", "balanced")
        if decision_style == "analytical_strategic":
            return max(options, key=lambda x: x.get("efficiency", 0))
        elif decision_style == "evidence_based":
            return max(options, key=lambda x: x.get("evidence_quality", 0))
        elif decision_style == "logic_driven":
            return max(options, key=lambda x: x.get("technical_score", 0))
        elif decision_style == "opportunistic_aggressive":
            return max(options, key=lambda x: x.get("speed", 0))
        elif decision_style == "statistical_empirical":
            return max(options, key=lambda x: x.get("data_quality", 0))
        elif decision_style == "creative_intuitive":
            return max(options, key=lambda x: x.get("engagement_score", 0))
        elif decision_style == "speed_optimized":
            return max(options, key=lambda x: x.get("speed", 0))
        else:
            return options[len(options) // 2] if options else {}

    def get_personality_description(self) -> str:
        return f"""
Agent: {self.name}
Type: {self.personality.get('decision_making', 'Unknown')}
Style: {self.communication_style}
Risk: {self.personality.get('risk_tolerance', 'Unknown')}
Strength: {self.personality.get('strength', 'Unknown')}
Weakness: {self.personality.get('weakness', 'Unknown')}
Platform: {deployment_config.platform}
Model: {self.model_config.get('model')}
""".strip()
