from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
import asyncio
import time
import iroh
from .node import RaggyNode
from .veracity import VeracityRail

@dataclass
class Relationship:
    entity_id: str
    trust_score: float = 0.0
    last_interaction: float = field(default_factory=time.time)
    interaction_count: int = 0
    flags: Set[str] = field(default_factory=set)

class CooperationEngine:
    def __init__(self, node: RaggyNode):
        self.node = node
        self.relationships: Dict[str, Relationship] = {}
        self._relationship_doc = None
        
    async def initialize(self):
        # Create relationship document
        self._relationship_doc = await self.node._node.docs.create()
        await self._save_relationships()
        
    async def _save_relationships(self):
        if self._relationship_doc:
            relationships_data = {
                k: v.__dict__ for k, v in self.relationships.items()
            }
            await self._relationship_doc.set_bytes(
                b"relationships",
                str(relationships_data).encode()
            )
            
    async def _load_relationships(self):
        if self._relationship_doc:
            data = await self._relationship_doc.get_bytes(b"relationships")
            if data:
                relationships_data = eval(data.decode())
                self.relationships = {
                    k: Relationship(**v) for k, v in relationships_data.items()
                }
                
    async def add_relationship(self, entity_id: str) -> Relationship:
        rel = Relationship(entity_id=entity_id)
        self.relationships[entity_id] = rel
        await self._save_relationships()
        return rel
        
    async def update_relationship(
        self,
        entity_id: str,
        trust_delta: float = 0.0,
        flags: Optional[Set[str]] = None
    ) -> Optional[Relationship]:
        if entity_id in self.relationships:
            rel = self.relationships[entity_id]
            rel.trust_score = max(0.0, min(1.0, rel.trust_score + trust_delta))
            rel.last_interaction = time.time()
            rel.interaction_count += 1
            if flags:
                rel.flags.update(flags)
            await self._save_relationships()
            return rel
        return None
        
    async def defederate(self, entity_id: str, reason: str):
        if entity_id in self.relationships:
            rel = self.relationships[entity_id]
            rel.flags.add(f"defederated:{reason}")
            rel.trust_score = 0.0
            await self._save_relationships()
            
            # Notify network of defederation
            await self.node._node.gossip.publish({
                "type": "defederation",
                "source_id": self.node.id,
                "target_id": entity_id,
                "reason": reason
            })
