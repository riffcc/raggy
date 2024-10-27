import iroh

async def connect_node():
    """Create and start an iroh node"""
    node = iroh.IrohNode()
    await node.start()
    return node
