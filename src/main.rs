use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let (_, hash) = raggy::create_iroh_node().await?;
    
    println!("hash: {hash}");
    
    Ok(())
}
