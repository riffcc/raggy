import asyncio
from iroh_node import IrohNode

async def main():
    # Create node
    node = await IrohNode.create_memory_node()
    print("Node created successfully")
    
    # Get and print node ID
    node_id = await node.get_node_id()
    print(f"Node ID: {node_id}")
    
    # Get and print default author
    author = await node.get_default_author()
    print(f"Default author: {author}")
    
    # Create and print doc
    doc = await node.create_doc()
    print(f"Created doc with ID: {doc.id()}")
    
    # Cleanup
    await node.shutdown()
    print("Node shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
