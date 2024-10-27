import pytest
import iroh
import asyncio

@pytest.mark.asyncio
async def test_iroh_node_start():
    options = iroh.NodeOptions(gc_interval_millis=1000, blob_events=True)
    options.enable_docs = True
    node = await iroh.Iroh.memory_with_options(options)
    node_id = await node.net().node_id()
    assert node_id is not None

@pytest.mark.asyncio
async def test_default_author():
    options = iroh.NodeOptions(gc_interval_millis=1000, blob_events=True)
    options.enable_docs = True
    node = await iroh.Iroh.memory_with_options(options)
    author = await node.authors().default()
    assert author is not None

@pytest.mark.asyncio
async def test_document_creation():
    options = iroh.NodeOptions()
    options.enable_docs = True
    node = await iroh.Iroh.memory_with_options(options)
    doc = await node.docs().create()
    assert doc.id() is not None
