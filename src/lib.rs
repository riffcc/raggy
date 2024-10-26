use anyhow::Result;
use iroh::client::Client as Iroh;

pub async fn create_iroh_node() -> Result<(Iroh, String, String, String)> {
    // Create in memory iroh node
    let node = Iroh::memory().await?;
    let node_id = node.net().node_id().await?;
    println!("Started Iroh node: {}", node_id);

    let author = node.authors().default().await?;
    println!("Default author: {}", author);

    let doc = node.docs().create().await?;
    println!("Created doc: {}", doc.id());

    Ok((node, node_id.to_string(), author.to_string(), doc.id().to_string()))
}
