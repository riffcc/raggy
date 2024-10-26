import iroh
import asyncio
from typing import Optional

class IrohNode:
    def __init__(self):
        self.instance: Optional[iroh.Iroh] = None
    
    @classmethod
    async def create_memory_node(cls) -> 'IrohNode':
        """Create a new in-memory Iroh node"""
        node = cls()
        node.instance = await iroh.Iroh.memory()
        return node
    
    async def get_node_id(self) -> str:
        """Get the node's ID"""
        if not self.instance:
            raise RuntimeError("Node not initialized")
        return await self.instance.net().node_id()
    
    async def create_author(self):
        """Get or create the default author for the node"""
        if not self.instance:
            raise RuntimeError("Node not initialized")
        return await self.instance.authors().default()
    
    async def create_doc(self):
        """Create a new document"""
        if not self.instance:
            raise RuntimeError("Node not initialized")
        return await self.instance.docs().create()
    
    async def shutdown(self):
        """Cleanup and shutdown the node"""
        if self.instance:
            # Add proper cleanup if needed
            self.instance = None
