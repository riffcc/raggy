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

    # Assuming document creation is sufficient for this test
    assert main_doc.id() is not None
    assert ticket_write_doc.id() is not None

@pytest.mark.asyncio
async def test_document_join():
    options = iroh.NodeOptions(gc_interval_millis=1000, blob_events=False)
    options.enable_docs = True
    node = await iroh.Iroh.memory_with_options(options)
    
    # Create a document and share it
    doc = await node.docs().create()
    write_ticket = await doc.share(iroh.ShareMode.WRITE, iroh.AddrInfoOptions.ID)
    
    # Join the document using the ticket
    joined_doc = await node.docs().join(write_ticket)
    
    # Verify that the joined document has the same ID
    assert joined_doc.id() == doc.id()
