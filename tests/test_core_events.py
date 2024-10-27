import pytest
from raggy import Raggy

async def test_core_event_emission():
    """Test event emission from core"""
    raggy = await Raggy.create()
    received = None
    
    async def handler(event):
        nonlocal received
        received = event
    
    raggy.events.on("test_event", handler)
    await raggy.emit("test_event", {"test": "data"})
    
    assert received is not None
    assert received.name == "test_event"
    assert received.data == {"test": "data"}
    assert received.source == "core"
