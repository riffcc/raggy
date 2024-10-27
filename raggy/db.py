import iroh
from typing import Optional, Dict, Any
from dataclasses import dataclass
import asyncio

@dataclass
class IrohDoc:
    id: str
    data: Dict[str, Any]
    tickets: Dict[str, str]

class RaggyDB:
    def __init__(self):
        self.client = None
        self.docs: Dict[str, IrohDoc] = {}
        
    @classmethod
    async def create(cls) -> 'RaggyDB':
        self = cls()
        node = iroh.Node()
        await node.start()
        await node.enable_docs()
        self.client = node
        return self
        
    async def create_doc(self, name: str) -> IrohDoc:
        doc = await self.client.docs.create()
        iroh_doc = IrohDoc(
            id=doc.id.hex(),
            data={},
            tickets={"read": (await doc.share()).hex()}
        )
        self.docs[name] = iroh_doc
        return iroh_doc
        
    async def get_doc(self, name: str) -> Optional[IrohDoc]:
        return self.docs.get(name)
        
    async def set_value(self, doc_name: str, key: str, value: Any):
        doc = await self.get_doc(doc_name)
        if not doc:
            raise KeyError(f"Document {doc_name} not found")
        doc_handle = await self.client.docs.get(bytes.fromhex(doc.id))
        await doc_handle.set_bytes(key.encode(), str(value).encode())
        doc.data[key] = value
        
    async def get_value(self, doc_name: str, key: str) -> Any:
        doc = await self.get_doc(doc_name)
        if not doc:
            raise KeyError(f"Document {doc_name} not found")
        doc_handle = await self.client.docs.get(bytes.fromhex(doc.id))
        value = await doc_handle.get_bytes(key.encode())
        return value.decode() if value else None

