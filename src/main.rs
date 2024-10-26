use anyhow::Result;
use iroh::sync::store::BlobStore;

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
    match node.blobs().import_bytes(content).await {
        Ok(blob_hash) => println!("Created blob with hash: {}", blob_hash),
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
        let blob_hash = node.blobs().import_bytes(content).await?;
        assert!(!blob_hash.to_string().is_empty());

        // Test blob retrieval
        let mut out = Vec::new();
        node.blobs().export_to_vec(&blob_hash, &mut out).await?;
        assert_eq!(&out, content);

        // Test non-existent blob
        let invalid_hash = iroh::hash::Hash::new([0; 32]);
        let mut out = Vec::new();
        assert!(node.blobs().export_to_vec(&invalid_hash, &mut out).await.is_err());

        Ok(())
    }
}