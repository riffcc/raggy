from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import asyncio
import iroh

@dataclass
class VeracityRail:
    source_id: str
    target_id: str
    dimensions: Dict[str, float] = field(default_factory=dict)
    
    def total_weight(self) -> float:
        if not self.dimensions:
            return 0.0
        return sum(self.dimensions.values()) / len(self.dimensions)

class VeracitySystem:
    def __init__(self, node):
        self.node = node
        self.rails: Dict[str, Dict[str, VeracityRail]] = {}
        
    async def initialize(self):
        pass
        
    async def create_rail(
        self,
        target_id: str,
        dimensions: Dict[str, float]
    ) -> VeracityRail:
        rail = VeracityRail(
            source_id=self.node.id,
            target_id=target_id,
            dimensions=dimensions
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
        
    async def update_rail_dimension(
        self,
        target_id: str,
        dimension: str,
        value: float
    ) -> Optional[VeracityRail]:
        if (self.node.id in self.rails and 
            target_id in self.rails[self.node.id]):
            rail = self.rails[self.node.id][target_id]
            rail.dimensions[dimension] = value
            return rail
        return None
        
    def get_rail(self, target_id: str) -> Optional[VeracityRail]:
        return self.rails.get(self.node.id, {}).get(target_id)
