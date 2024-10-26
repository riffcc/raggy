import asyncio
from iroh_node import IrohNode

async def main():
    # Create node
    node = await IrohNode.create_memory_node()
    print("Node created successfully")
    
    # Get and print node ID
    node_id = await node.get_node_id()
    print(f"Node ID: {node_id}")
    
    # Create new author
    author = await node.create_author()
    if author:
        print(f"Created new author: {author}")
    else:
        print("Failed to create author, continuing anyway...")
    
    # Create and print doc
    try:
        doc = await node.create_doc()
        print(f"Created doc with ID: {doc.id()}")
    except Exception as e:
        print(f"Failed to create document: {e}")
    
    # Cleanup
    await node.shutdown()
    print("Node shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
