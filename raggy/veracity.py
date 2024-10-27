from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import asyncio
import iroh
from .node import RaggyNode

@dataclass
class VeracityRail:
    source_id: str
    target_id: str
    semantic_closeness: float = 0.0
    physical_proximity: float = 0.0
    logical_proximity: float = 0.0
    common_goals: float = 0.0
    alignment: float = 0.0
    shared_history: float = 0.0
    
    def total_weight(self) -> float:
        weights = [
            self.semantic_closeness,
            self.physical_proximity,
            self.logical_proximity,
            self.common_goals,
            self.alignment,
            self.shared_history
        ]
        return sum(weights) / len(weights)

class VeracitySystem:
    def __init__(self, node: RaggyNode):
        self.node = node
        self.rails: Dict[str, Dict[str, VeracityRail]] = {}
        
    async def create_rail(
        self,
        target_id: str,
        semantic_closeness: float = 0.0,
        physical_proximity: float = 0.0,
        logical_proximity: float = 0.0,
        common_goals: float = 0.0,
        alignment: float = 0.0,
        shared_history: float = 0.0
    ) -> VeracityRail:
        rail = VeracityRail(
            source_id=self.node.id,
            target_id=target_id,
            semantic_closeness=semantic_closeness,
            physical_proximity=physical_proximity,
            logical_proximity=logical_proximity,
            common_goals=common_goals,
            alignment=alignment,
            shared_history=shared_history
        )
        
        if self.node.id not in self.rails:
            self.rails[self.node.id] = {}
        self.rails[self.node.id][target_id] = rail
        
        # Create shared document for the rail
        doc = await self.node._node.docs.create()
        await doc.set_bytes(b"rail", str(rail.__dict__).encode())
        
        # Share with target
        ticket = await doc.share(capabilities=["write"])
        await self.node._node.gossip.publish({
            "type": "rail_created",
            "source_id": self.node.id,
            "target_id": target_id,
            "ticket": ticket.hex()
        })
        
        return rail
        
    async def update_rail(
        self,
        target_id: str,
        **updates
    ) -> Optional[VeracityRail]:
        if (self.node.id in self.rails and 
            target_id in self.rails[self.node.id]):
            rail = self.rails[self.node.id][target_id]
            for k, v in updates.items():
                if hasattr(rail, k):
                    setattr(rail, k, v)
            return rail
        return None
        
    def get_rail(self, target_id: str) -> Optional[VeracityRail]:
        return self.rails.get(self.node.id, {}).get(target_id)
