# Raggy P2P
A simple libp2p node implementation in Rust that demonstrates basic peer-to-peer networking capabilities.

## Features

- Basic libp2p node setup
- Ping protocol implementation
- Automatic peer discovery
- TCP transport with noise encryption and yamux multiplexing

## Building

Make sure you have Rust installed. Then run:

```bash
cargo build
```

## Running

To start the node:

```bash
cargo run
```

The node will start and listen on a random port. It will display its PeerId and listening address when started.
