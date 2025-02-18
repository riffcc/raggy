use clap::Parser;
use futures::StreamExt;
use libp2p::{
    gossipsub::{self, IdentTopic, MessageAuthenticity},
    identify,
    identity,
    kad::{store::MemoryStore, Behaviour as KademliaBehaviour, Config as KademliaConfig, Event as KademliaEvent, QueryResult, RecordKey},
    mdns,
    multiaddr::Protocol,
    PeerId,
    ping,
    swarm::{SwarmEvent, NetworkBehaviour, Config},
    Multiaddr,
    Swarm,
    Transport,
};
use std::{error::Error, time::Duration, collections::HashSet, sync::Arc, hash::{Hash, Hasher, DefaultHasher}};
use tokio::{time::interval, sync::Mutex};

const GOSSIP_TOPIC: &str = "raggy-chat";
const GOSSIP_INTERVAL: u64 = 10; // seconds

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    /// Port to listen on
    #[arg(short, long, default_value_t = 0)]
    port: u16,

    /// Node name
    #[arg(short, long, default_value = "anonymous")]
    name: String,
}

#[derive(NetworkBehaviour)]
#[behaviour(out_event = "MyBehaviourEvent")]
struct MyBehaviour {
    ping: ping::Behaviour,
    identify: identify::Behaviour,
    kademlia: KademliaBehaviour<MemoryStore>,
    mdns: mdns::tokio::Behaviour,
    gossipsub: gossipsub::Behaviour,
}

#[derive(Debug)]
enum MyBehaviourEvent {
    Ping(ping::Event),
    Identify(identify::Event),
    Kademlia(KademliaEvent),
    Mdns(mdns::Event),
    Gossipsub(gossipsub::Event),
}

impl From<ping::Event> for MyBehaviourEvent {
    fn from(event: ping::Event) -> Self {
        MyBehaviourEvent::Ping(event)
    }
}

impl From<identify::Event> for MyBehaviourEvent {
    fn from(event: identify::Event) -> Self {
        MyBehaviourEvent::Identify(event)
    }
}

impl From<KademliaEvent> for MyBehaviourEvent {
    fn from(event: KademliaEvent) -> Self {
        MyBehaviourEvent::Kademlia(event)
    }
}

impl From<mdns::Event> for MyBehaviourEvent {
    fn from(event: mdns::Event) -> Self {
        MyBehaviourEvent::Mdns(event)
    }
}

impl From<gossipsub::Event> for MyBehaviourEvent {
    fn from(event: gossipsub::Event) -> Self {
        MyBehaviourEvent::Gossipsub(event)
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    
    // Use empty callback for the main binary
    let message_callback = Arc::new(Mutex::new(HashSet::new()));
    let args: Vec<String> = std::env::args().collect();
    
    raggy_p2p::run_node(args, message_callback).await
}

// New function that accepts a message callback for testing
pub async fn run_node(
    args: Vec<String>,
    message_callback: Arc<Mutex<HashSet<String>>>,
) -> Result<(), Box<dyn Error>> {
    // Parse command line arguments using the vector
    let cli = Cli::try_parse_from(args)?;

    // Create a random PeerId
    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = PeerId::from(local_key.public());
    println!("Local peer id: {local_peer_id}");

    // Create transport with TCP and QUIC support
    let transport = {
        let tcp = libp2p::tcp::tokio::Transport::new(libp2p::tcp::Config::default())
            .upgrade(libp2p::core::upgrade::Version::V1)
            .authenticate(libp2p::noise::Config::new(&local_key).unwrap())
            .multiplex(libp2p::yamux::Config::default())
            .map(|(peer_id, muxer), _| (peer_id, libp2p::core::muxing::StreamMuxerBox::new(muxer)));

        let quic = libp2p::quic::tokio::Transport::new(libp2p::quic::Config::new(&local_key))
            .map(|(peer_id, conn), _| (peer_id, libp2p::core::muxing::StreamMuxerBox::new(conn)));

        // Combine the transports and map the Either type to a single type
        libp2p::core::transport::OrTransport::new(tcp, quic)
            .map(|either, _| match either {
                futures::future::Either::Left((peer_id, muxer)) => (peer_id, muxer),
                futures::future::Either::Right((peer_id, muxer)) => (peer_id, muxer),
            })
            .boxed()
    };

    // Create the identify service
    let identify = identify::Behaviour::new(identify::Config::new(
        "/raggy/1.0.0".to_string(),
        local_key.public(),
    ).with_agent_version(format!("raggy/{}", env!("CARGO_PKG_VERSION"))));

    // Set up Kademlia DHT with more aggressive settings
    let mut cfg = KademliaConfig::default();
    cfg.set_query_timeout(Duration::from_secs(5 * 60));
    cfg.set_record_ttl(Some(Duration::from_secs(60)));
    cfg.set_publication_interval(Some(Duration::from_secs(30)));
    // Use NonZeroUsize for replication factor
    cfg.set_replication_factor(std::num::NonZeroUsize::new(3).unwrap());
    let store = MemoryStore::new(local_peer_id);
    let kademlia = KademliaBehaviour::with_config(local_peer_id, store, cfg);

    // Set up mDNS for local peer discovery
    let mdns = mdns::tokio::Behaviour::new(mdns::Config::default(), local_peer_id)?;

    // Set up GossipSub with more lenient settings
    let gossipsub_config = gossipsub::ConfigBuilder::default()
        .heartbeat_interval(Duration::from_secs(1))
        .validation_mode(gossipsub::ValidationMode::Permissive) // Be more permissive about message validation
        .message_id_fn(|message: &gossipsub::Message| {         // Content-address messages
            let mut s = DefaultHasher::new();
            message.data.hash(&mut s);
            gossipsub::MessageId::from(s.finish().to_string())
        })
        .mesh_n_low(1)           // Lower mesh expectations
        .mesh_n(3)               // Aim for 3 peers in mesh
        .mesh_n_high(5)          // Allow up to 5 peers in mesh
        .gossip_lazy(1)          // Require fewer peers for gossip
        .history_length(10)      // Keep more message history
        .history_gossip(3)       // Gossip more history
        .build()
        .expect("Valid config");

    let mut gossipsub = gossipsub::Behaviour::new(
        MessageAuthenticity::Signed(local_key),
        gossipsub_config,
    )?;

    // Create a topic
    let topic = IdentTopic::new(GOSSIP_TOPIC);
    
    // Subscribe to the topic
    gossipsub.subscribe(&topic)?;

    // Create the network behaviour
    let behaviour = MyBehaviour {
        ping: ping::Behaviour::new(ping::Config::new()),
        identify,
        kademlia,
        mdns,
        gossipsub,
    };

    // Create a Swarm to manage peers and events
    let mut swarm = Swarm::new(
        transport,
        behaviour,
        local_peer_id,
        Config::with_tokio_executor(),
    );

    // Track our listening ports
    let mut tcp_port = None;
    let mut quic_port = None;

    // Listen on multiple protocols for better connectivity
    swarm.listen_on(format!("/ip4/0.0.0.0/tcp/{}", cli.port).parse()?)?;
    swarm.listen_on(format!("/ip4/0.0.0.0/udp/{}/quic-v1", cli.port).parse()?)?;
    
    // Also try to listen on IPv6 if available
    if let Ok(_) = swarm.listen_on("/ip6/::/tcp/0".parse()?) {
        println!("Listening on IPv6 TCP");
    }
    if let Ok(_) = swarm.listen_on("/ip6/::/udp/0/quic-v1".parse()?) {
        println!("Listening on IPv6 QUIC");
    }

    // Bootstrap with public DHT nodes
    let bootstrap_nodes = vec![
        "/dnsaddr/bootstrap.libp2p.io/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN",
        "/dnsaddr/bootstrap.libp2p.io/p2p/QmQCU2EcMqAqQPR2i9bChDtGNJchTbq5TbXJJ16u19uLTa",
        "/dnsaddr/bootstrap.libp2p.io/p2p/QmbLHAnMoJPWSCR5Zhtx6BHJX9KiKNN6tpvbUcqanj75Nb",
        // Add more bootstrap nodes from IPFS
        "/dnsaddr/bootstrap.libp2p.io/p2p/QmcZf59bWwK5XFi76CZX8cbJ4BhTzzA3gU1ZjYZcYW3dwt",
        "/ip4/104.131.131.82/tcp/4001/p2p/QmaCpDMGvV2BGHeYERUEnRQAwe3N8SzbUtfsmvsqQLuvuJ",
    ];

    // Create a record key for our namespace
    let record_key = RecordKey::new(&format!("/raggy/peers/{}", local_peer_id));

    // Set up more frequent DHT peer search interval
    let mut search_interval = interval(Duration::from_secs(15));  // More frequent searches

    // Set up periodic message broadcast interval
    let mut broadcast_interval = interval(Duration::from_secs(GOSSIP_INTERVAL));

    // Set up periodic bootstrap interval
    let mut bootstrap_interval = interval(Duration::from_secs(300));  // Rebootstrap every 5 minutes

    // Main event loop
    loop {
        tokio::select! {
            event = swarm.select_next_some() => {
                match event {
                    SwarmEvent::NewListenAddr { address, .. } => {
                        println!("Listening on {}", address);
                        
                        // Track ports from new listen addresses
                        for protocol in address.iter() {
                            match protocol {
                                Protocol::Tcp(port) => {
                                    tcp_port = Some(port);
                                }
                                Protocol::Udp(port) => {
                                    if address.iter().any(|p| matches!(p, Protocol::QuicV1)) {
                                        quic_port = Some(port);
                                    }
                                }
                                _ => {}
                            }
                        }

                        // Try to announce our external addresses if we have a public IP
                        if let Some(public_ip) = public_ip::addr().await {
                            println!("Public IP detected: {}", public_ip);
                            
                            if let Some(port) = tcp_port {
                                let tcp_addr: Multiaddr = format!("/ip4/{}/tcp/{}", public_ip, port).parse()?;
                                println!("Adding external TCP address: {}", tcp_addr);
                                swarm.add_external_address(tcp_addr.clone());
                                // Add this address to Kademlia
                                swarm.behaviour_mut().kademlia.add_address(&local_peer_id, tcp_addr);
                            }
                            
                            if let Some(port) = quic_port {
                                let quic_addr: Multiaddr = format!("/ip4/{}/udp/{}/quic-v1", public_ip, port).parse()?;
                                println!("Adding external QUIC address: {}", quic_addr);
                                swarm.add_external_address(quic_addr.clone());
                                // Add this address to Kademlia
                                swarm.behaviour_mut().kademlia.add_address(&local_peer_id, quic_addr);
                            }
                        }

                        // Also add local addresses to Kademlia
                        swarm.behaviour_mut().kademlia.add_address(&local_peer_id, address.clone());

                        // Store our addresses in the DHT
                        let mut addresses = Vec::new();
                        
                        // Add local address with peer ID
                        let mut addr_with_peer = address.clone();
                        addr_with_peer.push(Protocol::P2p(local_peer_id.into()));
                        addresses.push(addr_with_peer);

                        // Add external addresses with peer ID if we have a public IP
                        if let Some(public_ip) = public_ip::addr().await {
                            if let Some(port) = tcp_port {
                                let mut tcp_addr: Multiaddr = format!("/ip4/{}/tcp/{}", public_ip, port).parse()?;
                                tcp_addr.push(Protocol::P2p(local_peer_id.into()));
                                addresses.push(tcp_addr);
                            }
                            if let Some(port) = quic_port {
                                let mut quic_addr: Multiaddr = format!("/ip4/{}/udp/{}/quic-v1", public_ip, port).parse()?;
                                quic_addr.push(Protocol::P2p(local_peer_id.into()));
                                addresses.push(quic_addr);
                            }
                        }

                        // Store all our addresses in the DHT
                        let addresses_str = addresses.iter()
                            .map(|addr| addr.to_string())
                            .collect::<Vec<_>>()
                            .join(",");
                        
                        if let Err(e) = swarm.behaviour_mut().kademlia.put_record(
                            libp2p::kad::Record {
                                key: record_key.clone(),
                                value: addresses_str.as_bytes().to_vec(),
                                publisher: None,
                                expires: None,
                            },
                            libp2p::kad::Quorum::One
                        ) {
                            println!("Failed to store addresses in DHT: {}", e);
                        }

                        // After we're listening, connect to bootstrap nodes
                        for addr in &bootstrap_nodes {
                            let remote: Multiaddr = addr.parse()?;
                            println!("Dialing bootstrap node: {remote}");
                            if let Some(Protocol::P2p(hash)) = remote.iter().find(|p| matches!(p, Protocol::P2p(_))) {
                                let peer_id = PeerId::from(hash);
                                swarm.behaviour_mut().kademlia.add_address(&peer_id, remote.clone());
                                swarm.behaviour_mut().gossipsub.add_explicit_peer(&peer_id);
                                if let Err(e) = swarm.dial(remote.clone()) {
                                    println!("Failed to dial bootstrap node {}: {}", remote, e);
                                }
                            }
                        }
                        // Start bootstrapping process
                        if let Err(e) = swarm.behaviour_mut().kademlia.bootstrap() {
                            println!("Failed to bootstrap DHT: {e}");
                        }
                    }
                    SwarmEvent::Behaviour(event) => {
                        match event {
                            MyBehaviourEvent::Kademlia(kad_event) => match kad_event {
                                KademliaEvent::RoutingUpdated { peer, .. } => {
                                    println!("Routing table updated for peer: {peer}");
                                    // Add the peer to GossipSub as well
                                    swarm.behaviour_mut().gossipsub.add_explicit_peer(&peer);
                                }
                                KademliaEvent::OutboundQueryProgressed { result, .. } => {
                                    match result {
                                        QueryResult::GetRecord(Ok(ok)) => {
                                            println!("GetRecord query completed");
                                            match ok {
                                                libp2p::kad::GetRecordOk::FoundRecord(record) => {
                                                    // Parse the multiaddresses from the record
                                                    if let Ok(addresses_str) = String::from_utf8(record.record.value) {
                                                        for addr_str in addresses_str.split(',') {
                                                            if let Ok(addr) = addr_str.parse::<Multiaddr>() {
                                                                // Extract peer ID from the address if present
                                                                if let Some(Protocol::P2p(hash)) = addr.iter().find(|p| matches!(p, Protocol::P2p(_))) {
                                                                    let peer_id = PeerId::from(hash);
                                                                    if peer_id != local_peer_id {  // Don't dial ourselves
                                                                        println!("Found peer address in DHT: {}", addr);
                                                                        swarm.behaviour_mut().kademlia.add_address(&peer_id, addr.clone());
                                                                        swarm.behaviour_mut().gossipsub.add_explicit_peer(&peer_id);
                                                                        if let Err(e) = swarm.dial(addr.clone()) {
                                                                            println!("Failed to dial address {}: {}", addr, e);
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                                libp2p::kad::GetRecordOk::FinishedWithNoAdditionalRecord { .. } => {
                                                    println!("No additional records found");
                                                }
                                            }
                                        }
                                        QueryResult::GetProviders(Ok(_ok)) => {
                                            // Ignore provider events - we're not using them
                                        }
                                        QueryResult::StartProviding(Ok(_)) => {
                                            // Ignore provider events - we're not using them
                                        }
                                        QueryResult::Bootstrap(Ok(ok)) => {
                                            println!("Bootstrap completed with peer: {}", ok.peer);
                                            swarm.behaviour_mut().gossipsub.add_explicit_peer(&ok.peer);
                                            // After bootstrap, get the peer's addresses
                                            let key = RecordKey::new(&format!("/raggy/peers/{}", ok.peer));
                                            swarm.behaviour_mut().kademlia.get_record(key);
                                        }
                                        QueryResult::GetClosestPeers(Ok(ok)) => {
                                            println!("GetClosestPeers query completed");
                                            for peer in ok.peers {
                                                if peer != local_peer_id {  // Don't dial ourselves
                                                    println!("Found close peer: {}", peer);
                                                    swarm.behaviour_mut().gossipsub.add_explicit_peer(&peer);
                                                    // Get the peer's addresses from DHT
                                                    let key = RecordKey::new(&format!("/raggy/peers/{}", peer));
                                                    swarm.behaviour_mut().kademlia.get_record(key);
                                                }
                                            }
                                        }
                                        QueryResult::GetRecord(Err(e)) => {
                                            println!("GetRecord query failed: {e:?}");
                                        }
                                        QueryResult::GetProviders(Err(_)) => {
                                            // Ignore provider errors - we're not using them
                                        }
                                        QueryResult::StartProviding(Err(_)) => {
                                            // Ignore provider errors - we're not using them
                                        }
                                        QueryResult::Bootstrap(Err(e)) => {
                                            println!("Bootstrap query failed: {e:?}");
                                        }
                                        QueryResult::GetClosestPeers(Err(e)) => {
                                            println!("GetClosestPeers query failed: {e:?}");
                                        }
                                        _ => {}
                                    }
                                }
                                KademliaEvent::InboundRequest { request } => {
                                    println!("Received inbound Kademlia request: {request:?}");
                                }
                                _ => {}
                            },
                            MyBehaviourEvent::Identify(event) => {
                                println!("Identify event: {event:?}");
                                match event {
                                    identify::Event::Received { peer_id, info, .. } => {
                                        println!("Received identify info from {}: {:?}", peer_id, info);
                                        // Add their listen addresses to Kademlia
                                        for addr in info.listen_addrs {
                                            swarm.behaviour_mut().kademlia.add_address(&peer_id, addr);
                                        }
                                        // Add their observed address of us to our external addresses
                                        println!("Peer {} observes us as {}", peer_id, info.observed_addr);
                                        swarm.add_external_address(info.observed_addr.clone());
                                        // Also add it to Kademlia
                                        swarm.behaviour_mut().kademlia.add_address(&local_peer_id, info.observed_addr);
                                        // Add the peer to GossipSub
                                        swarm.behaviour_mut().gossipsub.add_explicit_peer(&peer_id);
                                    }
                                    identify::Event::Sent { peer_id } => {
                                        println!("Sent identify info to {}", peer_id);
                                    }
                                    identify::Event::Pushed { peer_id, info } => {
                                        println!("Received pushed identify update from {}: {:?}", peer_id, info);
                                        // Update addresses in Kademlia
                                        for addr in info.listen_addrs {
                                            swarm.behaviour_mut().kademlia.add_address(&peer_id, addr);
                                        }
                                        // Add their observed address of us
                                        println!("Peer {} now observes us as {}", peer_id, info.observed_addr);
                                        swarm.add_external_address(info.observed_addr.clone());
                                        swarm.behaviour_mut().kademlia.add_address(&local_peer_id, info.observed_addr);
                                    }
                                    identify::Event::Error { peer_id, error } => {
                                        println!("Identify error with {}: {}", peer_id, error);
                                    }
                                }
                            }
                            MyBehaviourEvent::Mdns(event) => {
                                match event {
                                    mdns::Event::Discovered(list) => {
                                        for (peer_id, multiaddr) in list {
                                            println!("mDNS discovered a new peer: {peer_id}");
                                            swarm.behaviour_mut().kademlia.add_address(&peer_id, multiaddr);
                                            // Add the peer to GossipSub
                                            swarm.behaviour_mut().gossipsub.add_explicit_peer(&peer_id);
                                        }
                                    }
                                    mdns::Event::Expired(list) => {
                                        for (peer_id, _multiaddr) in list {
                                            println!("mDNS discover peer has expired: {peer_id}");
                                        }
                                    }
                                }
                            }
                            MyBehaviourEvent::Gossipsub(gossip_event) => {
                                if let gossipsub::Event::Message {
                                    propagation_source: peer_id,
                                    message_id: id,
                                    message,
                                } = gossip_event
                                {
                                    let msg_str = String::from_utf8_lossy(&message.data).to_string();
                                    println!(
                                        "Got message: '{}' with id: {} from peer: {:?}",
                                        msg_str,
                                        id,
                                        peer_id
                                    );
                                    // Store message in callback for testing
                                    message_callback.lock().await.insert(msg_str);
                                }
                            }
                            MyBehaviourEvent::Ping(event) => {
                                println!("Ping event: {event:?}");
                            }
                        }
                    }
                    _ => {}
                }
            }
            _ = search_interval.tick() => {
                println!("Searching for peers in DHT...");
                // Get addresses of all known peers from the DHT
                let peers: Vec<_> = swarm.behaviour_mut().kademlia.kbuckets()
                    .into_iter()
                    .flat_map(|bucket| {
                        bucket.iter()
                            .filter(|entry| entry.node.key.preimage() != &local_peer_id)
                            .map(|entry| entry.node.key.preimage().clone())
                            .collect::<Vec<_>>()
                    })
                    .collect();
                
                // Now we can modify the swarm
                for peer in peers {
                    let key = RecordKey::new(&format!("/raggy/peers/{}", peer));
                    swarm.behaviour_mut().kademlia.get_record(key);
                }
            }
            _ = bootstrap_interval.tick() => {
                println!("Rebootstrapping DHT...");
                if let Err(e) = swarm.behaviour_mut().kademlia.bootstrap() {
                    println!("Failed to rebootstrap DHT: {e}");
                }
            }
            _ = broadcast_interval.tick() => {
                let message = format!("HELO FROM {}", cli.name);
                if let Err(e) = swarm
                    .behaviour_mut()
                    .gossipsub
                    .publish(topic.clone(), message.as_bytes())
                {
                    println!("Failed to publish message: {e}");
                }
            }
        }
    }
} 