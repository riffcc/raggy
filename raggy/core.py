from dataclasses import dataclass
from typing import Optional, Dict, Any
import asyncio
import iroh
import streamlit as st
from .events import EventBus
from .node import RaggyNode

@dataclass
class RaggyConfig:
    iroh_port: int = 8080
    streamlit_port: int = 8501
    ollama_url: str = "http://localhost:11434"
    debug: bool = False

class Raggy:
    def __init__(self, config: Optional[RaggyConfig] = None):
        self.config = config or RaggyConfig()
        self.iroh = None
        self.state: Dict[str, Any] = {}
        self.events = EventBus()
        self.node = None
        
    @classmethod
    async def create(cls, config: Optional[RaggyConfig] = None) -> 'Raggy':
        self = cls(config)
        self.node = RaggyNode("core", self.events)
        await self.node.start()
        return self
        
    async def start(self):
        """Start all Raggy components"""
        if not self.node:
            self.node = RaggyNode("core", self.events)
        await self.node.start()
            
    async def emit(self, event_name: str, data: Any):
        await self.events.emit(event_name, data, "core")
