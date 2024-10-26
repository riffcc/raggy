use anyhow::Result;

#[tokio::test]
async fn test_create_iroh_node() -> Result<()> {
    let (node, node_id, author, doc_id) = raggy::create_iroh_node().await?;
    
    // Verify node is running
    assert!(node.net().is_running().await);
    
    // Verify we got valid string outputs
    assert!(!node_id.is_empty());
    assert!(!author.is_empty());
    assert!(!doc_id.is_empty());
    
    // Verify node_id matches the actual node
    assert_eq!(node_id, node.net().node_id().await?.to_string());
    
    Ok(())
}
