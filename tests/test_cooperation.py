import pytest
import asyncio
from raggy.cooperation import CooperationEngine, Relationship
from raggy.node import RaggyNode

async def test_relationship_creation():
    """Test relationship document creation and management"""
    node = RaggyNode("test_node")
    await node.start()
    
    coop = CooperationEngine(node)
    await coop.initialize()
    
    # Create relationship
    rel = await coop.add_relationship("entity1")
    assert isinstance(rel, Relationship)
    assert rel.entity_id == "entity1"
    assert rel.trust_score == 0.0
    
    # Verify relationship was saved
    saved_rel = coop.relationships.get("entity1")
    assert saved_rel is not None
    assert saved_rel.entity_id == "entity1"
    
    await node.stop()

async def test_relationship_updates():
    """Test relationship updates and persistence"""
    node = RaggyNode("test_node")
    await node.start()
    
    coop = CooperationEngine(node)
    await coop.initialize()
    
    # Create and update relationship
    rel = await coop.add_relationship("entity1")
    updated_rel = await coop.update_relationship(
        "entity1",
        trust_delta=0.5,
        flags={"active", "verified"}
    )
    
    assert updated_rel is not None
    assert updated_rel.trust_score == 0.5
    assert "active" in updated_rel.flags
    assert "verified" in updated_rel.flags
    assert updated_rel.interaction_count == 1
    
    await node.stop()

async def test_defederation():
    """Test defederation mechanism"""
    node = RaggyNode("test_node")
    await node.start()
    
    coop = CooperationEngine(node)
    await coop.initialize()
    
    # Create relationship and then defederate
    await coop.add_relationship("entity1")
    await coop.update_relationship("entity1", trust_delta=0.5)
    await coop.defederate("entity1", "suspicious_behavior")
    
    # Verify defederation
    rel = coop.relationships["entity1"]
    assert "defederated:suspicious_behavior" in rel.flags
    assert rel.trust_score == 0.0
    
    await node.stop()

async def test_sybil_resistance():
    """Test Sybil resistance through trust scoring"""
    node = RaggyNode("test_node")
    await node.start()
    
    coop = CooperationEngine(node)
    await coop.initialize()
    
    # Create multiple relationships
    entities = ["entity1", "entity2", "entity3"]
    for entity_id in entities:
        await coop.add_relationship(entity_id)
        
    # Simulate good behavior for entity1
    for _ in range(5):
        await coop.update_relationship("entity1", trust_delta=0.1)
        
    # Simulate suspicious behavior for entity2
    await coop.update_relationship("entity2", trust_delta=0.1)
    await coop.defederate("entity2", "suspicious_behavior")
    
    # Verify trust scores
    assert coop.relationships["entity1"].trust_score > 0.4  # Good behavior
    assert coop.relationships["entity2"].trust_score == 0.0  # Defederated
    assert coop.relationships["entity3"].trust_score == 0.0  # Neutral
    
    await node.stop()
