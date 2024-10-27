import pytest
from raggy.veracity import VeracitySystem, VeracityRail
from raggy.node import RaggyNode

async def test_rail_creation():
    """Test creating veracity rails with dynamic dimensions"""
    node = RaggyNode("test_node")
    await node.start()
    
    veracity = VeracitySystem(node)
    
    # Create a rail with custom dimensions
    dimensions = {
        "semantic_similarity": 0.8,
        "trust_level": 0.7,
        "shared_context": 0.9
    }
    
    rail = await veracity.create_rail(
        "target_node",
        dimensions=dimensions
    )
    
    assert rail is not None
    assert rail.source_id == "test_node"
    assert rail.target_id == "target_node"
    assert rail.dimensions == dimensions
    
    await node.stop()

async def test_rail_dimension_updates():
    """Test updating rail dimensions dynamically"""
    node = RaggyNode("test_node")
    await node.start()
    
    veracity = VeracitySystem(node)
    
    # Create initial rail
    rail = await veracity.create_rail(
        "target_node",
        dimensions={"initial_dim": 0.5}
    )
    
    # Add new dimension
    updated_rail = await veracity.update_rail_dimension(
        "target_node",
        "new_dimension",
        0.8
    )
    
    assert updated_rail is not None
    assert "new_dimension" in updated_rail.dimensions
    assert updated_rail.dimensions["new_dimension"] == 0.8
    assert updated_rail.dimensions["initial_dim"] == 0.5
    
    await node.stop()

async def test_rail_weight_calculation():
    """Test weight calculation with dynamic dimensions"""
    node = RaggyNode("test_node")
    await node.start()
    
    veracity = VeracitySystem(node)
    
    # Create rail with various dimensions
    dimensions = {
        "dim1": 0.8,
        "dim2": 0.6,
        "dim3": 0.7,
    }
    
    rail = await veracity.create_rail(
        "target_node",
        dimensions=dimensions
    )
    
    # Calculate total weight
    total = rail.total_weight()
    assert 0.0 <= total <= 1.0
    assert total == (0.8 + 0.6 + 0.7) / 3
    
    await node.stop()

async def test_empty_rail_weight():
    """Test weight calculation with no dimensions"""
    node = RaggyNode("test_node")
    await node.start()
    
    veracity = VeracitySystem(node)
    
    # Create rail with no dimensions
    rail = await veracity.create_rail(
        "target_node",
        dimensions={}
    )
    
    # Verify weight is 0 when no dimensions exist
    assert rail.total_weight() == 0.0
    
    await node.stop()