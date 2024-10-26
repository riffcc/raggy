use anyhow::Result;
use iroh::client::blobs::Client;
use iroh::hash::Hash;

#[tokio::main]
async fn main() -> Result<()> {
    // Create in memory iroh node with docs enabled
    let node = iroh::node::Node::memory()
        .enable_docs()
        .spawn()
        .await?;

    let node_id = node.net().node_id().await?;
    println!("Started Iroh node: {node_id}");

    let author = node.authors().default().await?;
    println!("Default author: {author}");

    let doc = node.docs().create().await?;
    println!("Created doc: {}", doc.id());
    // Create a blob
    let content = b"Hello, Iroh!";
    match node.blobs().add_bytes(content).await {
        Ok(res) => println!("Created blob with hash: {:?}", res.hash),
        Err(e) => eprintln!("Failed to create blob: {}", e),
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_node_creation() -> Result<()> {
        let node = iroh::node::Node::memory()
            .enable_docs()
            .spawn()
            .await?;
        
        // Test node_id
        let node_id = node.net().node_id().await?;
        assert!(!node_id.to_string().is_empty());

        // Test default author
        let author = node.authors().default().await?;
        assert!(!author.to_string().is_empty());

        // Test doc creation
        let doc = node.docs().create().await?;
        assert!(!doc.id().to_string().is_empty());

        Ok(())
    }

    #[tokio::test]
    async fn test_blob_operations() -> Result<()> {
        let node = iroh::node::Node::memory()
            .enable_docs()
            .spawn()
            .await?;

        // Test blob creation
        let content = b"Hello, Iroh!";
        let res = node.blobs().add_bytes(content).await?;
        assert!(!res.hash.to_string().is_empty());

        // Test blob retrieval
        let mut out = Vec::new();
        let blob = node.blobs().read_to_bytes(res.hash).await?;
        assert_eq!(blob, content);
        assert_eq!(&out, content);

        // Test non-existent blob
        let invalid_hash = Hash::new([0; 32]);
        assert!(node.blobs().read_to_bytes(invalid_hash).await.is_err());

        Ok(())
    }
}
