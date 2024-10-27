import pytest
import asyncio
from raggy.events import EventBus, Event

async def test_event_emission():
    """Test basic event emission and reception"""
    bus = EventBus()
    received_events = []
    
    async def handler(event: Event):
        received_events.append(event)
    
    # Register handler
    bus.on("test_event", handler)
    
    # Emit event
    await bus.emit("test_event", {"data": "test"}, "test_source")
    
    # Verify event was received
    assert len(received_events) == 1
    assert received_events[0].name == "test_event"
    assert received_events[0].data == {"data": "test"}
    assert received_events[0].source == "test_source"

async def test_multiple_handlers():
    """Test multiple handlers for same event"""
    bus = EventBus()
    count1 = 0
    count2 = 0
    
    async def handler1(event: Event):
        nonlocal count1
        count1 += 1
        
    async def handler2(event: Event):
        nonlocal count2
        count2 += 1
    
    bus.on("test_event", handler1)
    bus.on("test_event", handler2)
    
    await bus.emit("test_event", None, "test")
    
    assert count1 == 1
    assert count2 == 1

async def test_event_history():
    """Test event history tracking"""
    bus = EventBus()
    
    # Emit multiple events
    events = [
        ("event1", "data1"),
        ("event2", "data2"),
        ("event3", "data3")
    ]
    
    for name, data in events:
        await bus.emit(name, data, "test")
    
    # Verify history
    assert len(bus.history) == 3
    for i, (name, data) in enumerate(events):
        assert bus.history[i].name == name
        assert bus.history[i].data == data

async def test_event_causality():
    """Test events maintain causal ordering"""
    bus = EventBus()
    order = []
    
    async def slow_handler(event: Event):
        await asyncio.sleep(0.1)
        order.append(f"{event.name}_slow")
        
    async def fast_handler(event: Event):
        order.append(f"{event.name}_fast")
    
    bus.on("test_event", slow_handler)
    bus.on("test_event", fast_handler)
    
    await bus.emit("test_event", None, "test")
    
    # Both handlers should complete
    assert len(order) == 2
    # Fast handler should finish first
    assert order[0].endswith("_fast")
    assert order[1].endswith("_slow")
