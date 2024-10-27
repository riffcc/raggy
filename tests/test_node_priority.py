import pytest
import asyncio
from raggy.node import RaggyNode
from raggy.node_priority import PriorityLoader

async def test_priority_loader_creation():
    """Test priority loader initialization"""
    node = RaggyNode("test_node")
    await node.start()
    
    loader = PriorityLoader(node)
    assert loader.node == node
    assert len(loader.priority_queue) == 0
    
    await node.stop()

async def test_priority_queue_ordering():
    """Test that documents are loaded in priority order"""
    node = RaggyNode("test_node")
    await node.start()
    
    loader = PriorityLoader(node)
    
    # Add documents with different entropy values
    docs = [
        ("doc1", 0.5),
        ("doc2", 0.8),
        ("doc3", 0.2),
    ]
    
    for doc_id, entropy in docs:
        loader.add_priority_data(doc_id, entropy)
    
    # Verify order
    assert loader.priority_queue[0].doc_id == "doc2"  # Highest entropy
    assert loader.priority_queue[-1].doc_id == "doc3"  # Lowest entropy
    
    await node.stop()

async def test_priority_loading():
    """Test actual document loading"""
    node = RaggyNode("test_node")
    await node.start()
    
    loader = PriorityLoader(node)
    loaded_docs = []
    
    async def doc_loaded_handler(event):
        loaded_docs.append(event.data["doc_id"])
    
    node.events.on("doc_loaded", doc_loaded_handler)
    
    # Create and add test documents
    doc1 = await node._node.docs.create()
    doc2 = await node._node.docs.create()
    
    loader.add_priority_data(doc1.id.hex(), 0.8)
    loader.add_priority_data(doc2.id.hex(), 0.5)
    
    # Start loading
    task = asyncio.create_task(loader.start_loading())
    await asyncio.sleep(0.1)
    await loader.stop()
    await task
    
    # Verify documents were loaded in correct order
    assert len(loaded_docs) == 2
    assert loaded_docs[0] == doc1.id.hex()  # Higher entropy loaded first
    
    await node.stop()
