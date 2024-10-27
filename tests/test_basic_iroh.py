import pytest
import iroh
import asyncio

@pytest.mark.asyncio
async def test_iroh_node_start():
    options = iroh.NodeOptions(gc_interval_millis=1000, blob_events=False)
    options.enable_docs = True

    node = await iroh.Iroh.memory_with_options(options)
    node_id = await node.net().node_id()
    assert node_id is not None

@pytest.mark.asyncio
async def test_default_author():
    options = iroh.NodeOptions(gc_interval_millis=1000, blob_events=False)
    options.enable_docs = True
    node = await iroh.Iroh.memory_with_options(options)
    author = await node.authors().default()
    assert author is not None

@pytest.mark.asyncio
async def test_document_creation():
    options = iroh.NodeOptions(gc_interval_millis=1000, blob_events=False)
    options.enable_docs = True
    node = await iroh.Iroh.memory_with_options(options)
    main_doc = await node.docs().create()
    ticket_write_doc = await node.docs().create()

    assert main_doc.id() is not None
    assert ticket_write_doc.id() is not None

    await node.sync_document(main_doc)
    await node.sync_document(ticket_write_doc)

    assert node.is_document_synced(main_doc)
    assert node.is_document_synced(ticket_write_doc)
