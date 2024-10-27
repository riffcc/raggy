from typing import Optional, Dict, Any
import asyncio
import iroh
from .events import EventBus
from .systems import register_systems

class RaggyNode:
    def __init__(self, node_id: str, events: Optional[EventBus] = None):
        self.id = node_id
        self.events = events or EventBus()
        self._docs = {}
        self._running = False
        self._node = None
        self._systems = {}
        
        # Register systems
        register_systems(self)