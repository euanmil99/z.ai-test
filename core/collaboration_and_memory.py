"""collaboration_and_memory.py

Provides:
- Sophisticated inter-agent collaboration
- Perpetual (short+long term) memory for all agents with clever context-aware caching
- Memory sharing and contextual memory objects
to be used in SwarmForge dynamic agent system"""

import asyncio
import time
from typing import Dict, Any, Optional
from collections import deque
import threading
import pickle
from pathlib import Path

# Simple disk-backed persistent memory with context-aware caching
class PerpetualMemory:
    def __init__(self, 
                 db_path: str = './memory/', 
                 max_short_term: int = 100, 
                 max_long_term: int = 10000
                ):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.short_term = deque(maxlen=max_short_term)
        self.long_term = deque(maxlen=max_long_term)
        self.lock = threading.Lock()  # For disk ops
        self.load()

    def add_experience(self, context: Dict[str, Any], importance: float = 0.5):
        obj = {"context": context, "ts": time.time(), "importance": importance}
        self.short_term.append(obj)
        # Promote to long term if above threshold
        if importance >= 0.9:
            self.long_term.append(obj)
        self._save_async()

    def recall_recent(self, query: str = ''):
        # Simple keyword matching
        return [x for x in list(self.short_term) if query in str(x["context"])]

    def recall_historical(self, query: str = ''):
        return [x for x in list(self.long_term) if query in str(x["context"])]

    def share_memory(self, other: 'PerpetualMemory', context_keys: Optional[list] = None):
        # Share selected context objs with another agent
        with self.lock:
            for obj in self.short_term:
                if context_keys is None or any(k in obj["context"] for k in context_keys):
                    other.add_experience(obj["context"], obj["importance"])

    def _save_async(self):
        def _do_save():
            with self.lock:
                data = {
                    'short_term': list(self.short_term),
                    'long_term': list(self.long_term)
                }
                with open(self.db_path / 'perpetual_memory.pkl', 'wb') as f:
                    pickle.dump(data, f)
        threading.Thread(target=_do_save, daemon=True).start()

    def load(self):
        try:
            with open(self.db_path / 'perpetual_memory.pkl', 'rb') as f:
                data = pickle.load(f)
                self.short_term = deque(data.get('short_term', []), maxlen=self.short_term.maxlen)
                self.long_term = deque(data.get('long_term', []), maxlen=self.long_term.maxlen)
        except Exception:
            pass

    def cleanup(self):
        # Purge least important/old long-term items if DB is too big
        if len(self.long_term) > self.long_term.maxlen:
            self.long_term = deque(list(self.long_term)[-self.long_term.maxlen:], maxlen=self.long_term.maxlen)

# Contextual memory for each agent
class ContextualMemoryObject:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.perpetual = PerpetualMemory(db_path=f'./memory/{agent_id}')

    def remember(self, observation: Dict[str, Any], importance: float = 0.5):
        self.perpetual.add_experience(observation, importance)

    def recall(self, query:str = '', long_term:bool = False):
        if long_term:
            return self.perpetual.recall_historical(query)
        return self.perpetual.recall_recent(query)

    def share_with(self, other_memory: 'ContextualMemoryObject', keys: Optional[list]=None):
        self.perpetual.share_memory(other_memory.perpetual, keys)

# Event/message bus for dynamic collaboration
class AgentEventBus:
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}

    def register_agent(self, agent_id: str):
        self.queues[agent_id] = asyncio.Queue()

    async def send_event(self, agent_id: str, message: Dict[str, Any]):
        if agent_id in self.queues:
            await self.queues[agent_id].put(message)

    async def receive_event(self, agent_id: str, timeout: float = 0.5):
        if agent_id in self.queues:
            try:
                msg = await asyncio.wait_for(self.queues[agent_id].get(), timeout=timeout)
                return msg
            except asyncio.TimeoutError:
                return None
        return None

# Sample usage in agent logic
def collaborative_task(agent1, agent2, query):
    # Example of chaining agents and sharing context
    # agent1 does task and saves context
    observation = {"task": "intermediate_result", "result": "..."}
    agent1.memory.remember(observation, importance=1.0)
    # agent1 shares to agent2
    agent1.memory.share_with(agent2.memory, keys=["task"])
    # agent2 recalls context for next task
    history = agent2.memory.recall(long_term=True)
    return history
