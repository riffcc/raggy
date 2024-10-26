use anyhow::Result;
use iroh::node::Node;
use iroh::store::MemoryStore;

pub async fn create_iroh_node() -> Result<(Node<MemoryStore>, String)> {
    let node = iroh::node::Node::memory().spawn().await?;
    let client = node.client();
    let hash = client.blobs().add_bytes(b"some data".to_vec()).await?.hash;
    println!("hash: {}", hash);
    let hash_str = hash.to_string();

    Ok((node, hash_str))
}
