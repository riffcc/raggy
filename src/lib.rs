use iroh::{node::{Node, NodeBuilder}, sync::memory::MemoryStore};
use tokio::runtime::Runtime;

pub struct IrohNode {
    node: Node<MemoryStore>,
}

impl IrohNode {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let rt = Runtime::new()?;
        let node = rt.block_on(async {
            NodeBuilder::new()
                .with_memory_store()
                .build()
                .await
                .expect("Failed to create node")
        });

        Ok(Self { node })
    }

    pub async fn get_node_id(&self) -> String {
        self.node.id().to_string()
    }

    pub async fn create_doc(&self) -> Result<iroh::bytes::Hash, Box<dyn std::error::Error>> {
        let doc = self.node.doc_sync().create().await?;
        Ok(doc.hash())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_node_creation() {
        let node = IrohNode::new().unwrap();
        assert!(!node.get_node_id().await.is_empty());
    }

    #[tokio::test]
    async fn test_doc_creation() {
        let node = IrohNode::new().unwrap();
        let doc_hash = node.create_doc().await.unwrap();
        assert!(!doc_hash.to_string().is_empty());
    }
}
