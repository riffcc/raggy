use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let (_, node_id, author, doc_id) = raggy::create_iroh_node().await?;
    
    println!("Started Iroh node: {node_id}");
    println!("Default author: {author}");
    println!("Created doc: {doc_id}");
    
    Ok(())
}
