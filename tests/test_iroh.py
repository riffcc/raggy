import pytest
from raggy.db import RaggyDB, IrohDoc

async def test_iroh_boots():
    """Test that Iroh database can be created and initialized"""
    db = await RaggyDB.create()
    assert db is not None
    assert db.client is not None

async def test_doc_creation():
    """Test document creation and basic operations"""
    db = await RaggyDB.create()
    
    # Create a test document
    doc = await db.create_doc("test_doc")
    assert isinstance(doc, IrohDoc)
    assert doc.id is not None
    assert "read" in doc.tickets
    
    # Verify document was stored
    stored_doc = await db.get_doc("test_doc")
    assert stored_doc is not None
    assert stored_doc.id == doc.id

async def test_doc_operations():
    """Test document read/write operations"""
    db = await RaggyDB.create()
    
    # Create test document
    await db.create_doc("test_doc")
    
    # Test writing
    test_data = {"key": "value", "number": "42"}  # Values must be strings
    for k, v in test_data.items():
        await db.set_value("test_doc", k, v)
    
    # Test reading
    for k, v in test_data.items():
        value = await db.get_value("test_doc", k)
        assert value == v

async def test_doc_queries():
    """Test document querying capabilities"""
    db = await RaggyDB.create()
    
    # Create multiple test documents
    docs = ["doc1", "doc2", "doc3"]
    for name in docs:
        doc = await db.create_doc(name)
        await db.set_value(name, "type", name)
    
    # Verify all documents exist
    for name in docs:
        doc = await db.get_doc(name)
        assert doc is not None
        value = await db.get_value(name, "type")
        assert value == name

