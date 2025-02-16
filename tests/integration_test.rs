use std::collections::HashSet;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Mutex;
use tokio::time::sleep;

// Import the main binary as a module
use raggy_p2p;

#[tokio::test]
async fn test_three_node_communication() {
    // Initialize logging for tests
    let _ = env_logger::try_init();

    // Store received messages for verification
    let node1_messages = Arc::new(Mutex::new(HashSet::new()));
    let node2_messages = Arc::new(Mutex::new(HashSet::new()));
    let node3_messages = Arc::new(Mutex::new(HashSet::new()));

    // Spawn three nodes with different ports and names
    let node1_handle = tokio::spawn({
        let messages = node1_messages.clone();
        async move {
            let args = vec!["test".to_string(), "--port".to_string(), "8001".to_string(), "--name".to_string(), "node1".to_string()];
            raggy_p2p::run_node(args, messages).await.unwrap();
        }
    });

    let node2_handle = tokio::spawn({
        let messages = node2_messages.clone();
        async move {
            let args = vec!["test".to_string(), "--port".to_string(), "8002".to_string(), "--name".to_string(), "node2".to_string()];
            raggy_p2p::run_node(args, messages).await.unwrap();
        }
    });

    let node3_handle = tokio::spawn({
        let messages = node3_messages.clone();
        async move {
            let args = vec!["test".to_string(), "--port".to_string(), "8003".to_string(), "--name".to_string(), "node3".to_string()];
            raggy_p2p::run_node(args, messages).await.unwrap();
        }
    });

    // Wait for nodes to discover each other and exchange messages
    sleep(Duration::from_secs(30)).await;

    // Verify that each node received messages from the other nodes
    let node1_received = node1_messages.lock().await;
    let node2_received = node2_messages.lock().await;
    let node3_received = node3_messages.lock().await;

    assert!(node1_received.len() >= 2, "Node 1 should receive messages from nodes 2 and 3");
    assert!(node2_received.len() >= 2, "Node 2 should receive messages from nodes 1 and 3");
    assert!(node3_received.len() >= 2, "Node 3 should receive messages from nodes 1 and 2");

    // Verify specific messages
    assert!(node1_received.contains("HELO FROM node2"));
    assert!(node1_received.contains("HELO FROM node3"));
    assert!(node2_received.contains("HELO FROM node1"));
    assert!(node2_received.contains("HELO FROM node3"));
    assert!(node3_received.contains("HELO FROM node1"));
    assert!(node3_received.contains("HELO FROM node2"));

    // Clean up
    node1_handle.abort();
    node2_handle.abort();
    node3_handle.abort();
}

#[tokio::test]
async fn test_node_disconnect_reconnect() {
    // Initialize logging for tests
    let _ = env_logger::try_init();

    // Store received messages for verification
    let node1_messages = Arc::new(Mutex::new(HashSet::new()));
    let node2_messages = Arc::new(Mutex::new(HashSet::new()));

    // Spawn two nodes initially
    let node1_handle = tokio::spawn({
        let messages = node1_messages.clone();
        async move {
            let args = vec!["test".to_string(), "--port".to_string(), "8001".to_string(), "--name".to_string(), "node1".to_string()];
            raggy_p2p::run_node(args, messages).await.unwrap();
        }
    });

    let node2_handle = tokio::spawn({
        let messages = node2_messages.clone();
        async move {
            let args = vec!["test".to_string(), "--port".to_string(), "8002".to_string(), "--name".to_string(), "node2".to_string()];
            raggy_p2p::run_node(args, messages).await.unwrap();
        }
    });

    // Wait for initial connection and message exchange
    sleep(Duration::from_secs(15)).await;

    // Verify initial messages were exchanged
    {
        let node1_received = node1_messages.lock().await;
        let node2_received = node2_messages.lock().await;
        
        assert!(node1_received.contains("HELO FROM node2"), "Node 1 should receive messages from node 2");
        assert!(node2_received.contains("HELO FROM node1"), "Node 2 should receive messages from node 1");
    }

    // Disconnect node2 by aborting its task
    node2_handle.abort();
    sleep(Duration::from_secs(5)).await;

    // Clear node1's message set to verify new messages after reconnection
    node1_messages.lock().await.clear();

    // Reconnect node2 with the same configuration
    let node2_handle = tokio::spawn({
        let messages = node2_messages.clone();
        async move {
            let args = vec!["test".to_string(), "--port".to_string(), "8002".to_string(), "--name".to_string(), "node2".to_string()];
            raggy_p2p::run_node(args, messages).await.unwrap();
        }
    });

    // Wait for reconnection and new message exchange
    sleep(Duration::from_secs(15)).await;

    // Verify messages were exchanged after reconnection
    {
        let node1_received = node1_messages.lock().await;
        assert!(node1_received.contains("HELO FROM node2"), "Node 1 should receive messages from reconnected node 2");
    }

    // Clean up
    node1_handle.abort();
    node2_handle.abort();
} 