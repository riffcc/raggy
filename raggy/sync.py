from typing import Dict, Any
import asyncio
import iroh
from .node import RaggyNode
from .state import NodeState

class NodeSync:
    def __init__(self, node: RaggyNode):
        self.node = node
        self._sync_tasks = {}
        
    async def sync_from_ticket(self, ticket: str):
        doc = await self.node._node.docs.import_from_ticket(
            bytes.fromhex(ticket)
        )
        state_bytes = await doc.get_bytes(b"state")
        if state_bytes:
            state_dict = eval(state_bytes.decode())  # Safe since we control the state format
            state = NodeState(**state_dict)
            
            # Update peer list
            self.node.state.peers[state.id] = state
            
            # Sync all referenced documents
            for ticket_type in [b"main_read", b"main_write"]:
                if ticket_bytes := await doc.get_bytes(ticket_type):
                    await self.sync_from_ticket(ticket_bytes.decode())
                    
    async def start_sync(self):
        while True:
            try:
                msg = await self.node._node.gossip.next_message()
                if msg["type"] == "ticket_share":
                    await self.sync_from_ticket(msg["data"]["ticket"])
            except Exception as e:
                await self.node.events.emit("sync_error", str(e), self.node.id)
                await asyncio.sleep(1)