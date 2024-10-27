import iroh
import asyncio

async def main():
    try:
        # Enable docs
        options = iroh.NodeOptions(gc_interval_millis=1000, blob_events=False)
        options.enable_docs = True

        # Create in-memory Iroh node
        node = await iroh.Iroh.memory_with_options(options)
        node_id = await node.net().node_id()
        print(f"Started Iroh node: {node_id}")

        # Get the default author
        author = await node.authors().default()
        print(f"Default author: {author}")

        # Attempt to create a document
        main_doc = await node.docs().create()
        ticket_write_doc = await node.docs().create()

        # Sync documents
        await node.sync_document(main_doc)
        await node.sync_document(ticket_write_doc)

        print("Iroh node initialized and documents synced.")

    except iroh.iroh_ffi.IrohError as e:
        print(f"Encountered an Iroh error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

asyncio.run(main())
