import pytest
import asyncio
from raggy.distributed import DistributedNode

async def test_state_sync_timing():
    """Test node join and sync timing"""
    # Create bootstrap node
    bootstrap = DistributedNode("bootstrap")
    await bootstrap.start()
    
    # Create test data
    doc = await bootstrap._node.docs.create()
    await doc.set_bytes(b"test_key", b"test_value")
    
    # Get bootstrap ticket
    bootstrap_ticket = (await doc.share()).hex()
    
    # Create and join new node
    new_node = DistributedNode("new_node")
    await new_node.start()
    
    # Track join event
    join_time = None
    async def on_join(event):
        nonlocal join_time
        join_time = event.data["sync_time"]
    
    new_node.events.on("node_joined", on_join)
    
    # Join network
    await new_node.join_network(bootstrap_ticket)
    
    # Verify join completed and timing was recorded
    assert join_time is not None
    assert join_time > 0
    
    await bootstrap.stop()
    await new_node.stop()

async def test_node_rejoining():
    """Test node rejoining after disconnect"""
    node1 = DistributedNode("node1")
    node2 = DistributedNode("node2")
    
    await node1.start()
    await node2.start()
    
    # Create initial connection
    doc = await node1._node.docs.create()
    ticket = (await doc.share()).hex()
    await node2.join_network(ticket)
    
    # Stop and restart node2
    await node2.stop()
    node2 = DistributedNode("node2")
    await node2.start()
    await node2.join_network(ticket)
    
    # Verify reconnection
    assert "node1" in node2.state.peers
    
    await node1.stop()
    await node2.stop()

async def test_node_death():
    """Test handling of node death"""
    node1 = DistributedNode("node1")
    node2 = DistributedNode("node2")
    
    await node1.start()
    await node2.start()
    
    # Connect nodes
    doc = await node1._node.docs.create()
    ticket = (await doc.share()).hex()
    await node2.join_network(ticket)
    
    # Track death events
    death_event = None
    async def on_death(event):
        nonlocal death_event
        death_event = event
    
    node2.events.on("node_death", on_death)
    
    # Simulate node1 death
    await node1.stop()
    
    # Wait for death detection
    await asyncio.sleep(2)
    
    # Verify death was detected
    assert death_event is not None
    assert death_event.data["node_id"] == "node1"
    assert "node1" not in node2.state.peers
    
    await node2.stop()
