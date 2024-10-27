from typing import Dict, Any, List, Optional
import asyncio
import heapq
from dataclasses import dataclass
import iroh
from .node import RaggyNode

@dataclass
class DataPriority:
    entropy: float
    timestamp: float
    doc_id: str
    
    def __lt__(self, other):
        return (self.entropy, -self.timestamp) > (other.entropy, -other.timestamp)

class PriorityLoader:
    def __init__(self, node: RaggyNode):
        self.node = node
        self.priority_queue: List[DataPriority] = []
        self._loading = False
        
    def add_priority_data(self, doc_id: str, entropy: float):
        timestamp = asyncio.get_event_loop().time()
        heapq.heappush(
            self.priority_queue,
            DataPriority(entropy, timestamp, doc_id)
        )
        
    async def start_loading(self):
        self._loading = True
        while self._loading and self.priority_queue:
            priority = heapq.heappop(self.priority_queue)
            await self._load_doc(priority.doc_id)
            
    async def _load_doc(self, doc_id: str):
        try:
            doc = await self.node._node.docs.get(bytes.fromhex(doc_id))
            if doc:
                await self.node.events.emit(
                    "doc_loaded",
                    {"doc_id": doc_id},
                    self.node.id
                )
        except Exception as e:
            await self.node.events.emit(
                "load_error",
                {"doc_id": doc_id, "error": str(e)},
                self.node.id
            )
            
    async def stop(self):
        self._loading = False
