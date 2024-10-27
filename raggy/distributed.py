from typing import Dict, Optional, List
import asyncio
import time
from dataclasses import dataclass
from .node import RaggyNode
from .events import Event

@dataclass
class SyncMetrics:
    start_time: float
    end_time: Optional[float] = None
    bytes_synced: int = 0
    docs_synced: int = 0

class DistributedNode(RaggyNode):
    def __init__(self, node_id: str):
        super().__init__(node_id)
        self.sync_metrics: Dict[str, SyncMetrics] = {}
        self.alive = True
        
    async def start(self):
        await super().start()
        self.sync_metrics[self.id] = SyncMetrics(time.time())
        await self._start_heartbeat()
        
    async def _start_heartbeat(self):
        while self.alive:
            await self._node.gossip.publish({
                "type": "heartbeat",
                "node_id": self.id,
                "timestamp": time.time()
            })
            await asyncio.sleep(1)
            
    async def join_network(self, bootstrap_ticket: str):
        start_time = time.time()
        try:
            await self.sync_from_ticket(bootstrap_ticket)
            self.sync_metrics[self.id].end_time = time.time()
            await self.events.emit(
                "node_joined",
                {"sync_time": self.sync_metrics[self.id].end_time - start_time},
                self.id
            )
        except Exception as e:
            await self.events.emit("join_error", str(e), self.id)
            
    async def handle_node_death(self, dead_node_id: str):
        if dead_node_id in self.state.peers:
            del self.state.peers[dead_node_id]
            await self.events.emit(
                "node_death",
                {"node_id": dead_node_id},
                self.id
            )
            
    async def stop(self):
        self.alive = False
        await super().stop()
