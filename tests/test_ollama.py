import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock
from raggy.ollama import OllamaIntegration, OllamaConfig
from raggy.node import RaggyNode

async def test_ollama_initialization():
    """Test Ollama integration initialization"""
    node = RaggyNode("test_node")
    await node.start()
    
    ollama = OllamaIntegration(node)
    await ollama.initialize()
    
    assert ollama._config_doc is not None
    assert ollama.config.url == "http://localhost:11434"
    assert ollama.config.model == "llama2"
    
    await node.stop()

async def test_config_updates():
    """Test configuration updates"""
    node = RaggyNode("test_node")
    await node.start()
    
    ollama = OllamaIntegration(node)
    await ollama.initialize()
    
    # Update config
    await ollama.update_config(
        url="http://localhost:11435",
        model="codellama"
    )
    
    assert ollama.config.url == "http://localhost:11435"
    assert ollama.config.model == "codellama"
    
    # Verify persistence
    config_data = await ollama._config_doc.get_bytes(b"config")
    loaded_config = eval(config_data.decode())
    assert loaded_config["url"] == "http://localhost:11435"
    
    await node.stop()

@pytest.mark.asyncio
async def test_message_sending():
    """Test message sending and response handling"""
    node = RaggyNode("test_node")
    await node.start()
    
    ollama = OllamaIntegration(node)
    await ollama.initialize()
    
    # Mock httpx response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    async def mock_aiter_lines():
        yield json.dumps({"response": "Hello"})
        yield json.dumps({"response": " Raggy!"})
    mock_response.aiter_lines = mock_aiter_lines
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        response = await ollama.send_message("Hi!")
        
    assert response == "Hello Raggy!"
    assert len(ollama._conversation) == 2
    
    await node.stop()

@pytest.mark.asyncio
async def test_continuous_learning():
    """Test continuous learning mode"""
    node = RaggyNode("test_node")
    await node.start()
    
    ollama = OllamaIntegration(node)
    await ollama.initialize()
    
    # Mock message sending
    mock_responses = ["Interesting!", "Tell me more!"]
    mock_response_idx = 0
    
    async def mock_send_message(content: str):
        nonlocal mock_response_idx
        response = mock_responses[mock_response_idx % len(mock_responses)]
        mock_response_idx += 1
        return response
        
    ollama.send_message = mock_send_message
    
    # Start learning
    await ollama.start_continuous_learning()
    
    # Let it run briefly
    await asyncio.sleep(0.1)
    
    # Stop learning
    await ollama.stop_continuous_learning()
    
    assert len(ollama._conversation) > 0
    assert not ollama._learning
    
    await node.stop()

@pytest.mark.asyncio
async def test_model_switching():
    """Test model switching functionality"""
    node = RaggyNode("test_node")
    await node.start()
    
    ollama = OllamaIntegration(node)
    await ollama.initialize()
    
    # Track model switch events
    switch_event = None
    async def on_switch(event):
        nonlocal switch_event
        switch_event = event
    
    node.events.on("model_switched", on_switch)
    
    # Switch model
    await ollama.switch_model("codellama")
    
    assert ollama.config.model == "codellama"
    assert switch_event is not None
    assert switch_event.data["model"] == "codellama"
    
    await node.stop()
