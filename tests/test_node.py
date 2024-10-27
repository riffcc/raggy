import pytest
import asyncio
from raggy.node import RaggyNode
from raggy.sync import NodeSync

async def test_node_creation():
    """Test node creation and initialization"""
    node = RaggyNode("test_node")
    await node.start()
    
    assert node.id == "test_node"
    assert node._docs["main"] is not None
    assert node._docs["ticket_write"] is not None
    assert node._docs["ticket_read"] is not None
    
    # Verify MainDoc contains node state
    state_bytes = await node._docs["main"].get_bytes(b"state")
    assert state_bytes is not None
    
    await node.stop()

async def test_node_ticket_creation():
    """Test ticket creation and storage"""
    node = RaggyNode("test_node")
    await node.start()
    
    # Verify tickets are created and stored
    write_ticket = await node._docs["ticket_write"].get_bytes(b"main_write")
    read_ticket = await node._docs["ticket_read"].get_bytes(b"main_read")
    
    assert write_ticket is not None
    assert read_ticket is not None
    
    await node.stop()

async def test_node_sync():
    """Test node synchronization"""
    node1 = RaggyNode("node1")
    node2 = RaggyNode("node2")
    
    await node1.start()
    await node2.start()
    
    sync1 = NodeSync(node1)
    sync2 = NodeSync(node2)
    
    # Start sync tasks
    task1 = asyncio.create_task(sync1.start_sync())
    task2 = asyncio.create_task(sync2.start_sync())
    
    # Wait for nodes to discover each other
    await asyncio.sleep(1)
    
    # Verify nodes are in each other's peer lists
    assert "node2" in node1.state.peers
    assert "node1" in node2.state.peers
    
    # Clean up
    task1.cancel()
    task2.cancel()
    await node1.stop()
    await node2.stop()

async def test_node_gossip():
    """Test node gossip protocol"""
    node = RaggyNode("test_node")
    await node.start()
    
    # Simulate receiving a node join message
    await node._node.gossip.publish({
        "type": "node_join",
        "node_id": "other_node"
    })
    
    # Wait for gossip processing
    await asyncio.sleep(0.1)
    
    await node.stop()