use anyhow::Result;
use iroh::client::blobs::Client;
use iroh::client::blobs::{BlobStatus, BaoBlobSize};

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
    let content = Vec::from("Hello, Iroh!");
    match node.blobs().add_bytes(content.clone()).await {
        Ok(res) => {
            println!("Created blob with hash: {:?}", res.hash);
            // Assuming you want to check the status of the blob after creation
            let status = node.blobs().status(res.hash).await?;
            match status {
                BlobStatus::Complete { size } => println!("Blob is complete with size: {}", size),
                BlobStatus::Partial { size } => println!("Blob is incomplete with size: {:?}", size),
                BlobStatus::NotFound => println!("Blob not found"),
            }
        },
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
        let content = Vec::from("Hello, Iroh!");
        let res = node.blobs().add_bytes(content.clone()).await?;
        // Assuming you want to check the status of the blob after creation
        let status = node.blobs().status(res.hash).await?;
        assert!(matches!(status, BlobStatus::Complete { .. }));

        // Test blob retrieval
        let blob = node.blobs().read_to_bytes(res.hash).await?;
        assert_eq!(blob, content);

        // Test non-existent blob
        let invalid_hash = Hash::new([0; 32]);
        assert!(node.blobs().read_to_bytes(invalid_hash).await.is_err());

        Ok(())
    }
}
