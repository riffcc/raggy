from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
import asyncio
import time
import uuid
from .node import RaggyNode
from .events import Event

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
        
    async def _save_realities(self):
        if self._reality_doc:
            realities_data = {
                k: v.__dict__ for k, v in self.realities.items()
            }
            await self._reality_doc.set_bytes(
                b"realities",
                str(realities_data).encode()
            )
            
    async def create_reality(self, name: str, rules: Dict[str, Any] = None) -> Reality:
        reality_id = str(uuid.uuid4())
        reality = Reality(
            id=reality_id,
            name=name,
            rules=rules or {}
        )
        self.realities[reality_id] = reality
        await self._save_realities()
        return reality
        
    async def add_entity(
        self,
        reality_id: str,
        attributes: Dict[str, Any] = None
    ) -> Optional[Entity]:
        if reality_id in self.realities:
            entity_id = str(uuid.uuid4())
            entity = Entity(
                id=entity_id,
                attributes=attributes or {}
            )
            self.realities[reality_id].entities[entity_id] = entity
            await self._save_realities()
            return entity
        return None
        
    async def update_entity(
        self,
        reality_id: str,
        entity_id: str,
        attributes: Dict[str, Any] = None,
        relationships: Dict[str, float] = None
    ) -> Optional[Entity]:
        if (reality_id in self.realities and 
            entity_id in self.realities[reality_id].entities):
            entity = self.realities[reality_id].entities[entity_id]
            if attributes:
                entity.attributes.update(attributes)
            if relationships:
                entity.relationships.update(relationships)
            await self._save_realities()
            return entity
        return None
