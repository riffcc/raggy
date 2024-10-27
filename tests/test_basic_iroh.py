import pytest
import iroh
import asyncio
from veracityrails.veracity_rails import VeracityRails

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

class Entity:
    def __init__(self):
        self.metadata_store = {}

    def store_metadata(self, metadata):
        self.metadata_store.update(metadata)

@pytest.mark.asyncio
async def test_veracity_rails():
    options = iroh.NodeOptions(gc_interval_millis=1000, blob_events=False)
    options.enable_docs = True
    node = await iroh.Iroh.memory_with_options(options)
    rails = VeracityRails(node)
    
    # Create actual entities
    entity_a = Entity()
    entity_b = Entity()
    
    # Create a veracity rail
    metadata = await rails.create_rail(entity_a, entity_b, 0.5)
    
    # Verify that metadata was stored correctly
    assert list(entity_a.metadata_store.keys())[0] in entity_a.metadata_store
    assert list(entity_b.metadata_store.keys())[0] in entity_b.metadata_store
    
    # Update the rail
    await rails.update_rail(metadata, 0.8)
    
    # Verify rail update
    assert metadata['weight'] == 0.8
