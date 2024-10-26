use anyhow::Result;
use std::env;
use std::net::SocketAddr;
use config::{Config, File};
use tokenizers::Tokenizer;
use iroh::client::blobs::BlobStatus;
use axum::{
    routing::post,
    Router,
    Json,
    extract::State,
    response::IntoResponse,
};
use tower::ServiceExt;
use http::Request;

// Shared state for handlers
#[derive(Clone)]
struct AppState {
    token: String,
    tokenizer: Tokenizer,
}

pub async fn handle_talk(tokenizer: &Tokenizer, input: String) -> Result<Vec<u32>> {
    let encoding = tokenizer.encode(input, true)
        .map_err(|e| anyhow::anyhow!("Failed to encode input: {:?}", e))?;
    Ok(encoding.get_ids().to_vec())
}

// Axum handler
async fn talk_handler(
    State(state): State<AppState>,
    Json(input): Json<String>,
) -> Json<Vec<u32>> {
    match handle_talk(&state.tokenizer, input).await {
        Ok(tokens) => Json(tokens),
        Err(_) => Json(vec![]),
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Load configuration
    let mut settings = Config::default();
    settings.merge(File::with_name(&format!("{}/.raggy", env::var("HOME")?)).required(false))?;
    let token: String = settings.get("token").unwrap_or_default();

    // Initialize tokenizer once
    let tokenizer = Tokenizer::from_pretrained("bert-base-uncased", None)
        .map_err(|e| anyhow::anyhow!("Failed to initialize tokenizer: {}", e))?;

    let state = AppState {
        token,
        tokenizer,
    };

    // Set up Axum router
    let app = Router::new()
        .route("/talk", post(talk_handler))
        .with_state(state);

    let addr = SocketAddr::from(([127, 0, 0, 1], 3030));
    println!("Starting server on {}", addr);
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    // CLI interaction
    if let Some(arg) = env::args().nth(1) {
        if arg == "talk" {
            println!("Enter your message:");
            let mut input = String::new();
            std::io::stdin().read_line(&mut input)?;
            match handle_talk(&state.tokenizer, input).await {
                Ok(tokens) => println!("Tokens: {:?}", tokens),
                Err(e) => eprintln!("Error: {}", e),
            }
        }
    }

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
    use axum::http::StatusCode;
    use tower::ServiceExt;
    use http::Request;
    
    #[test]
    fn test_root_doc_creation() -> Result<()> {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let node = iroh::node::Node::memory()
                .enable_docs()
                .spawn()
                .await?;

            let root_doc = node.docs().create().await?;
            assert!(!root_doc.id().to_string().is_empty());

            Ok(())
        })
    }

    #[test]
    fn test_node_creation() -> Result<()> {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let node = iroh::node::Node::memory()
                .enable_docs()
                .spawn()
                .await?;
            
            let node_id = node.net().node_id().await?;
            assert!(!node_id.to_string().is_empty());

            let author = node.authors().default().await?;
            assert!(!author.to_string().is_empty());

            let doc = node.docs().create().await?;
            assert!(!doc.id().to_string().is_empty());

            Ok(())
        })
    }

    #[test]
    fn test_blob_creation() -> Result<()> {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let node = iroh::node::Node::memory()
                .enable_docs()
                .spawn()
                .await?;

            let content = Vec::from("Hello, Iroh!");
            let res = node.blobs().add_bytes(content.clone()).await?;
            let status = node.blobs().status(res.hash).await?;
            assert!(matches!(status, BlobStatus::Complete { .. }));

            Ok(())
        })
    }

    #[test]
    fn test_blob_retrieval() -> Result<()> {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let node = iroh::node::Node::memory()
                .enable_docs()
                .spawn()
                .await?;

            let content = Vec::from("Hello, Iroh!");
            let res = node.blobs().add_bytes(content.clone()).await?;
            let blob = node.blobs().read_to_bytes(res.hash).await?;
            assert_eq!(blob, content);

            Ok(())
        })
    }

    #[test]
    fn test_non_existent_blob_retrieval() -> Result<()> {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let node = iroh::node::Node::memory()
                .enable_docs()
                .spawn()
                .await?;

            let invalid_hash = [0u8; 32];
            assert!(node.blobs().read_to_bytes(invalid_hash.into()).await.is_err());

            Ok(())
        })
    }

    #[test]
    fn test_handle_talk() -> Result<()> {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let tokenizer = Tokenizer::from_pretrained("bert-base-uncased", None)
                .map_err(|e| anyhow::anyhow!("Failed to initialize tokenizer: {}", e))?;
            
            let input = "Hello, world!".to_string();
            let tokens = handle_talk(&tokenizer, input).await?;
            assert!(!tokens.is_empty());
            Ok(())
        })
    }

    #[test]
    fn test_api_talk() -> Result<()> {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            // Initialize app state
            let tokenizer = Tokenizer::from_pretrained("bert-base-uncased", None)
                .map_err(|e| anyhow::anyhow!("Failed to initialize tokenizer: {}", e))?;
            
            let state = AppState {
                token: "test_token".to_string(),
                tokenizer,
            };

            // Build app
            let app = Router::new()
                .route("/talk", post(talk_handler))
                .with_state(state);

            // Create test request
            let request = Request::builder()
                .method(http::Method::POST)
                .uri("/talk")
                .header(http::header::CONTENT_TYPE, mime::APPLICATION_JSON.as_ref())
                .body(axum::body::Body::from(
                    serde_json::to_string(&"Hello, world!").unwrap()
                ))
                .unwrap();

            // Send request
            let response = app
                .oneshot(request)
                .await
                .unwrap();

            assert_eq!(response.status(), StatusCode::OK);

            // Get response body
            let body = hyper::body::to_bytes(response.into_body()).await.unwrap();
            let tokens: Vec<u32> = serde_json::from_slice(&body).unwrap();
            assert!(!tokens.is_empty());

            Ok(())
        })
    }
}
