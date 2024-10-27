import pytest
from raggy.reality import RealityLayer, Reality, Entity
from raggy.node import RaggyNode

async def test_reality_creation():
    """Test reality creation and management"""
    node = RaggyNode("test_node")
    await node.start()
    
    reality = RealityLayer(node)
    await reality.initialize()
    
    # Create a reality
    test_reality = await reality.create_reality(
        "test_reality",
        rules={"gravity": 9.8}
    )
    
    assert isinstance(test_reality, Reality)
    assert test_reality.name == "test_reality"
    assert test_reality.rules["gravity"] == 9.8
    
    await node.stop()

async def test_entity_management():
    """Test entity creation and updates"""
    node = RaggyNode("test_node")
    await node.start()
    
    reality = RealityLayer(node)
    await reality.initialize()
    
    # Create reality and entity
    test_reality = await reality.create_reality("test_reality")
    entity = await reality.add_entity(
        test_reality.id,
        attributes={"position": [0, 0, 0]}
    )
    
    assert isinstance(entity, Entity)
    assert "position" in entity.attributes
    
    # Update entity
    updated_entity = await reality.update_entity(
        test_reality.id,
        entity.id,
        attributes={"velocity": [1, 0, 0]},
        relationships={"other_entity": 0.5}
    )
    
    assert updated_entity is not None
    assert updated_entity.attributes["velocity"] == [1, 0, 0]
    assert updated_entity.relationships["other_entity"] == 0.5
    
    await node.stop()
