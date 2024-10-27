from dataclasses import dataclass
from typing import Optional, Dict, Any
import asyncio
import iroh
import streamlit as st
from .events import EventBus

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
        
    @classmethod
    async def create(cls, config: Optional[RaggyConfig] = None) -> 'Raggy':
        self = cls(config)
        self.iroh = await iroh.IrohClient.create()
        return self
        
    async def start(self):
        """Start all Raggy components"""
        if not self.iroh:
            self.iroh = await iroh.IrohClient.create()
            
    async def emit(self, event_name: str, data: Any):
        await self.events.emit(event_name, data, "core")

