import pytest
import asyncio
from iroh_node import IrohNode

@pytest.mark.asyncio
async def test_node_creation():
    """Test basic Iroh node creation and management"""
    node = await IrohNode.create_memory_node()
    
    # Test node creation
    assert node.instance is not None
    
    # Test node ID retrieval
    node_id = await node.get_node_id()
    assert isinstance(node_id, str)
    assert len(node_id) > 0
    
    # Test getting default author
    author = await node.create_author()
    assert author is not None
    
    # Test doc creation
    doc = await node.create_doc()
    assert doc is not None
    assert doc.id() is not None

    # Cleanup
    await node.shutdown()
