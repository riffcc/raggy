import iroh
import asyncio
import logging
from typing import Optional, Any

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class IrohNode:
    def __init__(self):
        self.instance: Optional[iroh.Iroh] = None
        self._author = None
    
    @classmethod
    async def create_memory_node(cls) -> 'IrohNode':
        """Create a new in-memory Iroh node"""
        node = cls()
        node.instance = await iroh.Iroh.memory()
        logger.debug(f"Created memory node")
        return node
    
    async def get_node_id(self) -> str:
        """Get the node's ID"""
        if not self.instance:
            raise RuntimeError("Node not initialized")
        node_id = await self.instance.net().node_id()
        logger.debug(f"Got node ID: {node_id}")
        return node_id
    
    async def create_author(self):
        """Create a new author for the node"""
        if not self.instance:
            raise RuntimeError("Node not initialized")
        try:
            if not self._author:
                self._author = await self.instance.authors().create()
                logger.debug(f"Created new author: {self._author}")
            return self._author
        except Exception as e:
            logger.error(f"Failed to create author: {e}")
            raise
    
    async def create_doc(self) -> Any:
        """Create a new document"""
        if not self.instance:
            raise RuntimeError("Node not initialized")
        try:
            doc = await self.instance.documents().create("test doc")
            logger.debug(f"Created document: {doc}")
            return doc
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise
    
    async def shutdown(self):
        """Cleanup and shutdown the node"""
        if self.instance:
            try:
                # Just clear the instance since Iroh handles cleanup internally
                logger.debug("Node shutdown complete")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
            finally:
                self.instance = None
