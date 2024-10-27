import pytest
from iroh_example.main import connect_node

@pytest.mark.asyncio
async def test_connect_node():
    node = await connect_node()
    assert node is not None
    await node.stop()
