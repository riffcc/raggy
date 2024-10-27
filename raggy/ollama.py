from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import asyncio
import time
import httpx
import json
from .node import RaggyNode
from .events import Event

@dataclass
class OllamaConfig:
    url: str = "http://localhost:11434"
    model: str = "llama2"
    system_prompt: str = """You are talking to Raggy, a young and curious AI. 
    Be helpful, friendly and wise in teaching Raggy about the world."""
    continuous_learning: bool = False
    learning_interval: float = 60.0

class OllamaIntegration:
    def __init__(self, node: RaggyNode, config: Optional[OllamaConfig] = None):
        self.node = node
        self.config = config or OllamaConfig()
        self._client = httpx.AsyncClient()
        self._learning = False
        self._conversation: List[Dict[str, str]] = []
        
    async def initialize(self):
        self._config_doc = await self.node._node.docs.create()
        await self._save_config()
        
    async def _save_config(self):
        if self._config_doc:
            await self._config_doc.set_bytes(
                b"config",
                str(self.config.__dict__).encode()
            )
            
    async def update_config(self, **updates):
        for k, v in updates.items():
            if hasattr(self.config, k):
                setattr(self.config, k, v)
        await self._save_config()
        
    async def send_message(self, content: str) -> str:
        try:
            response = await self._client.post(
                f"{self.config.url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": content,
                    "system": self.config.system_prompt,
                }
            )
            response.raise_for_status()
            
            # Parse streaming response
            full_response = ""
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            full_response += data["response"]
                            # Emit progress event
                            await self.node.events.emit(
                                "ollama_response_progress",
                                {"text": data["response"]},
                                self.node.id
                            )
                    except json.JSONDecodeError:
                        continue
                        
            # Store in conversation history
            self._conversation.append({
                "role": "user",
                "content": content
            })
            self._conversation.append({
                "role": "assistant",
                "content": full_response
            })
            
            return full_response
            
        except Exception as e:
            await self.node.events.emit(
                "ollama_error",
                {"error": str(e)},
                self.node.id
            )
            raise
            
    async def switch_model(self, model_name: str):
        self.config.model = model_name
        await self._save_config()
        await self.node.events.emit(
            "model_switched",
            {"model": model_name},
            self.node.id
        )
        
    async def start_continuous_learning(self):
        self._learning = True
        self.config.continuous_learning = True
        await self._save_config()
        asyncio.create_task(self._continuous_learning_loop())
        
    async def stop_continuous_learning(self):
        self._learning = False
        self.config.continuous_learning = False
        await self._save_config()
        
    async def _continuous_learning_loop(self):
        while self._learning:
            try:
                # Generate a curious question based on conversation history
                if self._conversation:
                    last_response = self._conversation[-1]["content"]
                    question = await self.send_message(
                        f"Based on our last discussion about '{last_response}', "
                        "what's another interesting aspect you'd like to explore?"
                    )
                    await asyncio.sleep(self.config.learning_interval)
                else:
                    # Start with a general question
                    await self.send_message(
                        "What's an interesting topic you'd like to discuss?"
                    )
                    await asyncio.sleep(self.config.learning_interval)
            except Exception as e:
                await self.node.events.emit(
                    "learning_error",
                    {"error": str(e)},
                    self.node.id
                )
                await asyncio.sleep(5)  # Back off on error
