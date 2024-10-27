from typing import Optional
from .veracity import VeracitySystem
from .events import EventBus
from .cooperation import CooperationEngine
from .reality import RealityLayer
from .cognition import CognitionEngine
from .visual import VisualProcessor

from .ollama import OllamaIntegration

class RaggyNode:
    def __init__(self, node_id: str, events: Optional[EventBus] = None):
        self.node_id = node_id
        self.events = events
        self.veracity = VeracitySystem(self)
        self.cooperation = CooperationEngine(self)
        self.reality = RealityLayer(self)
        self.cognition = CognitionEngine(self)
        self.visual = VisualProcessor(self)
        self.ollama = OllamaIntegration(self)
        
    async def start(self):
        await self.cooperation.initialize()
        await self.reality.initialize()
        await self.cognition.initialize()
        await self.visual.initialize()
        await self.ollama.initialize()


