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
use std::{error::Error, time::Duration, collections::HashSet, sync::Arc};
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

    // Set up GossipSub
    let gossipsub_config = gossipsub::ConfigBuilder::default()
        .heartbeat_interval(Duration::from_secs(1))
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

    // Listen on multiple protocols for better connectivity
    swarm.listen_on("/ip4/0.0.0.0/tcp/0".parse()?)?;
    swarm.listen_on("/ip4/0.0.0.0/udp/0/quic-v1".parse()?)?;
    
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

    // After setting up swarm listening...
    
    // Announce our external addresses if we know them
    if let Some(public_ip) = public_ip::addr().await {
        let tcp_addr = format!("/ip4/{}/tcp/{}", public_ip, listen_port).parse()?;
        let quic_addr = format!("/ip4/{}/udp/{}/quic-v1", public_ip, listen_port).parse()?;
        swarm.add_external_address(tcp_addr);
        swarm.add_external_address(quic_addr);
    }

    // Main event loop
    loop {
        tokio::select! {
            event = swarm.select_next_some() => {
                match event {
                    SwarmEvent::NewListenAddr { address, .. } => {
                        println!("Listening on {address:?}");
                        // After we're listening, connect to bootstrap nodes
                        for addr in &bootstrap_nodes {
                            let remote: Multiaddr = addr.parse()?;
                            println!("Dialing bootstrap node: {remote}");
                            if let Some(Protocol::P2p(hash)) = remote.iter().find(|p| matches!(p, Protocol::P2p(_))) {
                                let peer_id = PeerId::from(hash);
                                swarm.behaviour_mut().kademlia.add_address(&peer_id, remote.clone());
                                swarm.behaviour_mut().gossipsub.add_explicit_peer(&peer_id);
                                // Actively try to dial the bootstrap node
                                if let Err(e) = swarm.dial(remote.clone()) {
                                    println!("Failed to dial bootstrap node {}: {}", remote, e);
                                }
                            }
                        }
                        // Start bootstrapping process
                        if let Err(e) = swarm.behaviour_mut().kademlia.bootstrap() {
                            println!("Failed to bootstrap DHT: {e}");
                        }

                        // Start providing our record
                        if let Err(e) = swarm.behaviour_mut().kademlia.start_providing(record_key.clone()) {
                            println!("Failed to start providing record: {e}");
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
                                        QueryResult::GetProviders(Ok(ok)) => {
                                            match ok {
                                                libp2p::kad::GetProvidersOk::FoundProviders { providers, .. } => {
                                                    println!("Found {} providers in DHT", providers.len());
                                                    for peer in providers {
                                                        println!("Attempting to connect to provider: {}", peer);
                                                        swarm.behaviour_mut().gossipsub.add_explicit_peer(&peer);
                                                        if let Err(e) = swarm.dial(peer) {
                                                            println!("Failed to dial peer {}: {}", peer, e);
                                                        }
                                                    }
                                                }
                                                libp2p::kad::GetProvidersOk::FinishedWithNoAdditionalRecord { closest_peers } => {
                                                    println!("No providers found, but got {} closest peers", closest_peers.len());
                                                    for peer in closest_peers {
                                                        println!("Attempting to connect to closest peer: {}", peer);
                                                        swarm.behaviour_mut().gossipsub.add_explicit_peer(&peer);
                                                        if let Err(e) = swarm.dial(peer) {
                                                            println!("Failed to dial peer {}: {}", peer, e);
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        QueryResult::StartProviding(Ok(ok)) => {
                                            println!("Successfully started providing record: {ok:?}");
                                        }
                                        QueryResult::Bootstrap(Ok(ok)) => {
                                            println!("Bootstrap completed with peer: {}", ok.peer);
                                            // Add bootstrap peer to GossipSub
                                            swarm.behaviour_mut().gossipsub.add_explicit_peer(&ok.peer);
                                        }
                                        _ => println!("Query progressed: {result:?}"),
                                    }
                                }
                                KademliaEvent::InboundRequest { request } => {
                                    println!("Received inbound request: {request:?}");
                                }
                                _ => {}
                            },
                            MyBehaviourEvent::Identify(event) => {
                                println!("Identify event: {event:?}");
                                if let identify::Event::Received { peer_id, info, .. } = event {
                                    // Add Kademlia addresses from identify
                                    for addr in info.listen_addrs {
                                        swarm.behaviour_mut().kademlia.add_address(&peer_id, addr);
                                    }
                                    // Add the peer to GossipSub
                                    swarm.behaviour_mut().gossipsub.add_explicit_peer(&peer_id);
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
                // Try both get_providers and get_closest_peers for better discovery
                swarm.behaviour_mut().kademlia.get_providers(record_key.clone());
                swarm.behaviour_mut().kademlia.get_closest_peers(local_peer_id);
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