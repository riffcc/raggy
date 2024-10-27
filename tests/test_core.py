import pytest
from raggy.core import Raggy, RaggyConfig
from raggy.events import EventBus

async def test_raggy_creation():
    raggy = await Raggy.create()
    assert raggy is not None
    assert isinstance(raggy.config, RaggyConfig)
    assert raggy.node is not None
    assert isinstance(raggy.events, EventBus)

async def test_raggy_custom_config():
    config = RaggyConfig(iroh_port=8081, debug=True)
    raggy = await Raggy.create(config)
    assert raggy.config.iroh_port == 8081
    assert raggy.config.debug is True

async def test_raggy_start():
    raggy = await Raggy.create()
    await raggy.start()
    assert raggy.iroh is not None
