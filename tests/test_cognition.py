import pytest
import asyncio
from raggy.cognition import CognitionEngine, Thought
from raggy.node import RaggyNode

async def test_thought_creation():
    """Test thought creation and management"""
    node = RaggyNode("test_node")
    await node.start()
    
    cognition = CognitionEngine(node)
    await cognition.initialize()
    
    # Create a thought
    thought = await cognition.add_thought("test thought")
    
    assert isinstance(thought, Thought)
    assert thought.content == "test thought"
    assert thought.entropy == 0.0
    
    await node.stop()

async def test_continuous_thinking():
    """Test continuous thinking process"""
    node = RaggyNode("test_node")
    await node.start()
    
    cognition = CognitionEngine(node)
    await cognition.initialize()
    
    # Add some thoughts
    thought1 = await cognition.add_thought("thought1")
    thought2 = await cognition.add_thought("thought2")
    
    # Create veracity rail between thoughts
    await node.veracity.create_rail(
        thought2.id,
        semantic_closeness=0.8
    )
    
    # Start thinking
    await cognition.start_thinking()
    
    # Let it think for a moment
    await asyncio.sleep(2)
    
    # Verify connections were evaluated
    assert thought1.id in cognition.thoughts
    assert len(thought1.connections) > 0
    assert thought1.entropy > 0
    
    await cognition.stop_thinking()
    await node.stop()

async def test_entropy_optimization():
    """Test entropy-based optimization"""
    node = RaggyNode("test_node")
    await node.start()
    
    cognition = CognitionEngine(node)
    await cognition.initialize()
    
    # Add thoughts with different connection patterns
    thought1 = await cognition.add_thought("thought1")
    thought2 = await cognition.add_thought("thought2")
    thought3 = await cognition.add_thought("thought3")
    
    # Create varied connections
    await node.veracity.create_rail(thought2.id, semantic_closeness=0.8)
    await node.veracity.create_rail(thought3.id, semantic_closeness=0.2)
    
    # Let the engine optimize
    await cognition._evaluate_connections()
    await cognition._optimize_entropy()
    
    # Verify entropy calculations
    assert thought1.entropy >= 0.0
    assert thought2.entropy >= 0.0
    assert thought3.entropy >= 0.0
    
    await node.stop()
