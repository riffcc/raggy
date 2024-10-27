import pytest
from raggy.veracity import VeracitySystem, VeracityRail
from raggy.node import RaggyNode

async def test_rail_creation():
    """Test creating veracity rails"""
    node = RaggyNode("test_node")
    await node.start()
    
    veracity = VeracitySystem(node)
    
    # Create a rail
    rail = await veracity.create_rail(
        "target_node",
        semantic_closeness=0.8,
        alignment=0.7
    )
    
    assert rail is not None
    assert rail.source_id == "test_node"
    assert rail.target_id == "target_node"
    assert rail.semantic_closeness == 0.8
    assert rail.alignment == 0.7
    
    await node.stop()

async def test_rail_weights():
    """Test rail weight calculations"""
    node = RaggyNode("test_node")
    await node.start()
    
    veracity = VeracitySystem(node)
    
    # Create rail with various weights
    rail = await veracity.create_rail(
        "target_node",
        semantic_closeness=0.8,
        physical_proximity=0.6,
        logical_proximity=0.7,
        common_goals=0.9,
        alignment=0.8,
        shared_history=0.5
    )
    
    # Calculate total weight
    total = rail.total_weight()
    assert 0.0 <= total <= 1.0
    assert total == (0.8 + 0.6 + 0.7 + 0.9 + 0.8 + 0.5) / 6
    
    await node.stop()

async def test_rail_updates():
    """Test updating rail weights"""
    node = RaggyNode("test_node")
    await node.start()
    
    veracity = VeracitySystem(node)
    
    # Create initial rail
    rail = await veracity.create_rail("target_node", semantic_closeness=0.5)
    
    # Update rail
    updated_rail = await veracity.update_rail(
        "target_node",
        semantic_closeness=0.8,
        alignment=0.7
    )
    
    assert updated_rail is not None
    assert updated_rail.semantic_closeness == 0.8
    assert updated_rail.alignment == 0.7
    
    await node.stop()

async def test_one_sided_rails():
    """Test one-sided rail creation"""
    node1 = RaggyNode("node1")
    node2 = RaggyNode("node2")
    
    await node1.start()
    await node2.start()
    
    veracity1 = VeracitySystem(node1)
    veracity2 = VeracitySystem(node2)
    
    # Create one-sided rail from node1 to node2
    rail = await veracity1.create_rail(
        "node2",
        semantic_closeness=0.8
    )
    
    # Verify rail exists in node1
    assert veracity1.get_rail("node2") is not None
    
    # Verify no rail exists in opposite direction
    assert veracity2.get_rail("node1") is None
    
    await node1.stop()
    await node2.stop()
