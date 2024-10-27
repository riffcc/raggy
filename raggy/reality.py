from .node import RaggyNode
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
import asyncio
import time
import uuid

@dataclass
class Entity:
    id: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    relationships: Dict[str, float] = field(default_factory=dict)

@dataclass
class Reality:
    id: str
    name: str
    entities: Dict[str, Entity] = field(default_factory=dict)
    rules: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class RealityLayer:
    def __init__(self, node: RaggyNode):
        self.node = node
        self.realities: Dict[str, Reality] = {}
        self._reality_doc = None
        
    async def initialize(self):
        self._reality_doc = await self.node._node.docs.create()
        await self._save_realities()