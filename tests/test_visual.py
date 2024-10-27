import pytest
import io
from PIL import Image
import numpy as np
from raggy.visual import VisualProcessor, VisualPattern
from raggy.node import RaggyNode

async def test_visual_processor_creation():
    """Test visual processor initialization"""
    node = RaggyNode("test_node")
    await node.start()
    
    processor = VisualProcessor(node)
    await processor.initialize()
    
    assert processor._pattern_doc is not None
    
    await node.stop()

async def test_pattern_extraction():
    """Test pattern extraction from image"""
    node = RaggyNode("test_node")
    await node.start()
    
    processor = VisualProcessor(node)
    await processor.initialize()
    
    # Create test image
    img = Image.new('RGB', (10, 10), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Process image
    patterns = await processor.process_image(img_bytes)
    
    assert len(patterns) == 100  # 10x10 image
    assert all(isinstance(p, VisualPattern) for p in patterns)
    assert all(p.color == (255, 0, 0) for p in patterns)  # All red
    
    await node.stop()

async def test_pattern_rails():
    """Test rail formation between patterns"""
    node = RaggyNode("test_node")
    await node.start()
    
    processor = VisualProcessor(node)
    await processor.initialize()
    
    # Create test image with two colors
    img = Image.new('RGB', (2, 1))
    img.putpixel((0, 0), (255, 0, 0))  # Red
    img.putpixel((1, 0), (255, 0, 0))  # Red
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Process image
    patterns = await processor.process_image(img_bytes)
    
    # Verify rails were created
    assert len(patterns) == 2
    pattern1, pattern2 = patterns
    
    # Check pattern connections
    assert pattern2.id in pattern1.connections
    assert pattern1.id in pattern2.connections
    
    # Check veracity rails
    rail = node.veracity.get_rail(pattern2.id)
    assert rail is not None
    assert rail.semantic_closeness > 0
    
    await node.stop()

async def test_pattern_persistence():
    """Test pattern storage and retrieval"""
    node = RaggyNode("test_node")
    await node.start()
    
    processor = VisualProcessor(node)
    await processor.initialize()
    
    # Create and process test image
    img = Image.new('RGB', (2, 2), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    await processor.process_image(img_bytes)
    
    # Verify patterns were saved
    saved_data = await processor._pattern_doc.get_bytes(b"patterns")
    assert saved_data is not None
    
    # Verify data can be loaded
    patterns_data = eval(saved_data.decode())
    assert len(patterns_data) == 4  # 2x2 image
    
    await node.stop()
