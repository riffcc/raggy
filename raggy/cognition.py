from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
import asyncio
import time
import math
from .node import RaggyNode
from .events import Event

@dataclass
class Thought:
    id: str
    content: Any
    connections: Dict[str, float] = field(default_factory=dict)
    entropy: float = 0.0
    timestamp: float = field(default_factory=time.time)

class CognitionEngine:
    def __init__(self, node: RaggyNode):
        self.node = node
        self.thoughts: Dict[str, Thought] = {}
        self._thought_doc = None
        self._thinking = False
        
    async def initialize(self):
        self._thought_doc = await self.node._node.docs.create()
        await self._save_thoughts()
        
    async def start_thinking(self):
        self._thinking = True
        asyncio.create_task(self._continuous_thinking())
        
    async def stop_thinking(self):
        self._thinking = False
        
    async def _continuous_thinking(self):
        while self._thinking:
            await self._evaluate_connections()
            await self._optimize_entropy()
            await asyncio.sleep(1)
            
    async def _evaluate_connections(self):
        for thought_id, thought in self.thoughts.items():
            for other_id, other in self.thoughts.items():
                if thought_id != other_id:
                    # Use veracity rails to weight connections
                    rail = self.node.veracity.get_rail(other_id)
                    if rail:
                        weight = rail.total_weight()
                        thought.connections[other_id] = weight
                        
    async def _optimize_entropy(self):
        for thought in self.thoughts.values():
            # Calculate entropy based on connection distribution
            probabilities = [w for w in thought.connections.values() if w > 0]
            if probabilities:
                entropy = -sum(p * math.log2(p) for p in probabilities)
                thought.entropy = entropy
                
    async def add_thought(self, content: Any) -> Thought:
        thought_id = str(time.time())
        thought = Thought(id=thought_id, content=content)
        self.thoughts[thought_id] = thought
        await self._save_thoughts()
        return thought
        
    async def _save_thoughts(self):
        if self._thought_doc:
            thoughts_data = {
                k: v.__dict__ for k, v in self.thoughts.items()
            }
            await self._thought_doc.set_bytes(
                b"thoughts",
                str(thoughts_data).encode()
            )
