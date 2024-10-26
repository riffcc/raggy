use anyhow::Result;
use iroh::node::Node;
use iroh::store::MemoryStore;

pub async fn create_iroh_node() -> Result<(Node<MemoryStore>, String, String, String)> {
    // Create in memory iroh node
    let node = Node::memory().spawn().await?;

    let node_id = node.net().node_id().await?;
    let node_id_str = node_id.to_string();

    let author = node.authors().default().await?;
    let author_str = author.to_string();

    let doc = node.docs().create().await?;
    let doc_id = doc.id().to_string();

    Ok((node, node_id_str, author_str, doc_id))
}
