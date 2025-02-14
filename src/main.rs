use clap::Parser;
use futures::StreamExt;
use libp2p::{
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
use std::{error::Error, time::Duration};
use tokio::time::interval;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    /// Port to listen on
    #[arg(short, long, default_value_t = 0)]
    port: u16,
}

#[derive(NetworkBehaviour)]
#[behaviour(to_swarm = "MyBehaviourEvent")]
struct MyBehaviour {
    ping: ping::Behaviour,
    identify: identify::Behaviour,
    kademlia: KademliaBehaviour<MemoryStore>,
    mdns: mdns::tokio::Behaviour,
}

#[derive(Debug)]
enum MyBehaviourEvent {
    Ping(ping::Event),
    Identify(identify::Event),
    Kademlia(KademliaEvent),
    Mdns(mdns::Event),
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

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    env_logger::init();

    // Parse command line arguments
    let cli = Cli::parse();

    // Create a random PeerId
    let local_key = identity::Keypair::generate_ed25519();
    let local_peer_id = PeerId::from(local_key.public());
    println!("Local peer id: {local_peer_id}");

    // Create a transport
    let transport = libp2p::tcp::tokio::Transport::default()
        .upgrade(libp2p::core::upgrade::Version::V1)
        .authenticate(libp2p::noise::Config::new(&local_key).unwrap())
        .multiplex(libp2p::yamux::Config::default())
        .boxed();

    // Create the identify service
    let identify = identify::Behaviour::new(identify::Config::new(
        "/raggy/1.0.0".to_string(),
        local_key.public(),
    ));

    // Set up Kademlia DHT
    let mut cfg = KademliaConfig::default();
    cfg.set_query_timeout(Duration::from_secs(5 * 60));
    // Enable record publishing
    cfg.set_record_ttl(Some(Duration::from_secs(60)));
    cfg.set_publication_interval(Some(Duration::from_secs(30)));
    let store = MemoryStore::new(local_peer_id);
    let kademlia = KademliaBehaviour::with_config(local_peer_id, store, cfg);

    // Set up mDNS for local peer discovery
    let mdns = mdns::tokio::Behaviour::new(mdns::Config::default(), local_peer_id)?;

    // Create the network behaviour
    let behaviour = MyBehaviour {
        ping: ping::Behaviour::new(ping::Config::new()),
        identify,
        kademlia,
        mdns,
    };

    // Create a Swarm to manage peers and events
    let mut swarm = Swarm::new(
        transport,
        behaviour,
        local_peer_id,
        Config::with_tokio_executor(),
    );

    // Listen on all interfaces and the specified port (0 means random port)
    swarm.listen_on(format!("/ip4/0.0.0.0/tcp/{}", cli.port).parse()?)?;

    // Bootstrap with public DHT nodes
    let bootstrap_nodes = vec![
        "/dnsaddr/bootstrap.libp2p.io/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN",
        "/dnsaddr/bootstrap.libp2p.io/p2p/QmQCU2EcMqAqQPR2i9bChDtGNJchTbq5TbXJJ16u19uLTa",
        "/dnsaddr/bootstrap.libp2p.io/p2p/QmbLHAnMoJPWSCR5Zhtx6BHJX9KiKNN6tpvbUcqanj75Nb",
    ];

    // Create a record key for our namespace
    let record_key = RecordKey::new(&format!("/raggy/peers/{}", local_peer_id));

    // Set up periodic DHT peer search interval
    let mut search_interval = interval(Duration::from_secs(30));

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
                            // Extract peer ID from the multiaddr
                            if let Some(Protocol::P2p(hash)) = remote.iter().find(|p| matches!(p, Protocol::P2p(_))) {
                                let peer_id = PeerId::from(hash);
                                swarm.behaviour_mut().kademlia.add_address(&peer_id, remote);
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
                                }
                                KademliaEvent::OutboundQueryProgressed { result, .. } => {
                                    match result {
                                        QueryResult::GetProviders(Ok(ok)) => {
                                            println!("Found peers in DHT");
                                            // The peers will be automatically connected to if we have their addresses
                                            // from the identify protocol
                                        }
                                        QueryResult::StartProviding(Ok(ok)) => {
                                            println!("Successfully started providing record: {ok:?}");
                                        }
                                        QueryResult::Bootstrap(Ok(ok)) => {
                                            println!("Bootstrap completed with peer: {}", ok.peer);
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
                                }
                            }
                            MyBehaviourEvent::Mdns(event) => {
                                match event {
                                    mdns::Event::Discovered(list) => {
                                        for (peer_id, multiaddr) in list {
                                            println!("mDNS discovered a new peer: {peer_id}");
                                            swarm.behaviour_mut().kademlia.add_address(&peer_id, multiaddr);
                                        }
                                    }
                                    mdns::Event::Expired(list) => {
                                        for (peer_id, _multiaddr) in list {
                                            println!("mDNS discover peer has expired: {peer_id}");
                                        }
                                    }
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
                // Periodically search for other peers
                println!("Searching for peers in DHT...");
                swarm.behaviour_mut().kademlia.get_providers(record_key.clone());
            }
        }
    }
} 