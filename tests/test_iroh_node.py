import pytest
import asyncio
from iroh_node import IrohNode

@pytest.mark.asyncio
async def test_node_creation():
    """Test basic Iroh node creation and management"""
    node = await IrohNode.create_memory_node()
    try:
        # Test node creation
        assert node.instance is not None
        
        # Test node ID retrieval
        node_id = await node.get_node_id()
        assert isinstance(node_id, str)
        assert len(node_id) > 0
    finally:
        await node.shutdown()

@pytest.mark.asyncio
async def test_author_creation():
    """Test author creation and caching"""
    node = await IrohNode.create_memory_node()
    try:
        # Test getting default author
        author1 = await node.create_author()
        assert author1 is not None
        
        # Test author caching
        author2 = await node.create_author()
        assert author2 is author1  # Should return cached author
    finally:
        await node.shutdown()

@pytest.mark.asyncio
async def test_doc_creation():
    """Test document creation"""
    node = await IrohNode.create_memory_node()
    try:
        doc = await node.create_doc()
        assert doc is not None
        assert doc.id is not None
    finally:
        await node.shutdown()

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for uninitialized node"""
    node = IrohNode()
    
    with pytest.raises(RuntimeError, match="Node not initialized"):
        await node.get_node_id()
    
    with pytest.raises(RuntimeError, match="Node not initialized"):
        await node.create_author()
    
    with pytest.raises(RuntimeError, match="Node not initialized"):
        await node.create_doc()

@pytest.mark.asyncio
async def test_shutdown_idempotency():
    """Test that shutdown can be called multiple times safely"""
    node = await IrohNode.create_memory_node()
    
    await node.shutdown()
    assert node.instance is None
    
    # Should not raise an error
    await node.shutdown()
    assert node.instance is None
