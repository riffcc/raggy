from typing import Any, Callable, Dict, List, Optional
import asyncio
import logging
from dataclasses import dataclass, field

@dataclass
class Event:
    name: str
    data: Any
    source: str
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())

class EventBus:
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}
        self.history: List[Event] = []
        self._running = False
        
    async def emit(self, event_name: str, data: Any, source: str):
        event = Event(event_name, data, source)
        self.history.append(event)
        
        if event_name in self.listeners:
            await asyncio.gather(
                *[listener(event) for listener in self.listeners[event_name]]
            )
            
    def on(self, event_name: str, callback: Callable):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)
        
    def off(self, event_name: str, callback: Callable):
        if event_name in self.listeners:
            self.listeners[event_name].remove(callback)
