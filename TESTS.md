# Tests

## Setup
Codebase: Python3 + Iroh
Features:
* Iroh acts as a persistence layer
* Cooperation Engine provides a way to allow diverse thoughts and ideas to be explored in parallel
* Defederation allows for prevention of Sybil behaviours
* Reality Layer allows for the creation of simulated realities
* Cognition Engine allows for the creation of The Mind

### Basics
## Initial tests
* Iroh boots and works correctly
    * Docs are enabled
    * Docs can be
        * Read
        * Written
        * Updated
        * Queried

## Event driven
* Everything in the entire codebase is event driven wherever possible
* Events are consistent and do not violate causality or other constraints
* All components listen for events and interact asynchronously as expected
* Events such as lost packets or failures of nodes do not break the system

### Iroh-specific
## Node-to-node functionality
* Nodes keep track of all of their own state through a main document, MainDoc
* MainDoc is the source of truth for all node state
* MainDoc can be updated only by the node that owns it
* TicketWriteDoc contains read/write tickets for everything in MainDoc
* TicketReadDoc contains read-only tickets for everything in MainDoc
* Syncing a document through either TicketWriteDoc or TicketReadDoc will synchronise all documents that are referenced to the node that requested the sync
* Nodes can be added and removed from the network at will, and will automatically sync their state with the network
    * They will use Iroh's gossip protocol to announce to the network that they joined and a ticket or channel that can be used to communicate with them
    * Nodes will use the gossip channel to submit bootstrap tickets to them.
    * They will use a single "bootstrap ticket" to sync their state with the network and pull down any necessary data.
    * They will then public a ticket to the gossip network to announce that they have joined and whatever tickets are needed to access their data.
    * Nodes will continually follow the gossip channel, loading Iroh tickets from it and examining them for any data that they think they need.
    * In this way, the gossip network forms a very highly available backbone

Major tests:
* Nodes create a MainDoc and keep it filled with the necessary data
* Nodes create a TicketWriteDoc and TicketReadDoc
* Nodes can sync documents through TicketWriteDoc and TicketReadDoc
* Nodes broadcast joining the network using Iroh's gossip protocol when they join
* Nodes broadcast their TicketReadDoc over the gossip network when a node joins
* Nodes each follow the gossip network and load any tickets from it that they need

### Expanded node-to-node functionality
* Priority loading of nodes
    * Specifically, we want to add a new node and have it sync the hottest/most entropic data first, allowing it to instantly start participating and loading in data.
    * A node should be able to start loading data and querying as soon as it joins, simply slowed down by slower retrieval times.

### Distributed systems tests
* State sync timing test
    * We should be able to measure the time it takes for a node to join and sync its state with the network.
* Node rejoining test
* Node death test
    * We should be able to kill a node instantly and not lose any data
    * Data from the node should be propagated to other nodes and the loss of that node should be detectable and handled by the network

## Veracity Rails (Trust Rails)
* Veracity Rails can exist linking any two entities together
* A shared document is created which both entities could influence or write to
* The document's CID (and one or more valid retrieval tickets for it) are added to each side of the rail - to each entity involved in the rail
* Rails can link together an arbitrary number of participants with different weightings from and to each entity
* The veracity rails are used to establish many kinds of dynamic weights
    * Semantic closeness - how close two entities are semantically
    * Physical proximity - how close two entities are physically
    * Logical proximity - how close two entities are logically
    * Common goals - how many goals two entities share
    * Alignment - how aligned two entities are
    * Shared history - how much shared history two entities have

Veracity rails can be used to filter things like reviews and other information down to just who you trust, and how much you trust them. They have many other uses too.

Veracity rails will be used by:
* Web UI to render ideas and thoughts and information
* The Cognition Engine and The Mind as the start of a weighted trust graph for each entity it wants to evaluate

Major tests:
* Veracity rails are correctly created and updated
* Veracity rails are referenced from both sides of a relationship
* Veracity rails can be created in a one-sided manner and still be correctly referenced from both sides
* Trust/veracity scores on an individual link can be adjusted at any time by the entity who owns the link

## Cooperation Engine + Defederation
* We should have each entity have relationships with an arbitrary set of other entities
* They should track this in a specific-to-the-entity RelationshipDoc
* We should be able to lookup the RelationshipDoc for any entity instantly
  * This will work by creating a DocID by taking the token's raw data and hashing it, then using that as a key to lookup the DocID in the Iroh network.
* Sybil resistance
    * We should be able to add and remove nodes from the network at will
    * Nodes should not be able to build up veracity rails without good behaviour

Major tests:
* RelationshipDoc is created correctly
* RelationshipDoc can be updated correctly
* RelationshipDoc doesn't lose data at any point

## Reality Layer and Cognition Engine
* Reality Layer creation and management
  * Simulated realities can be instantiated with unique parameters, entities and environments
  * Entities within the Reality Layer can interact with each other and the environment
  * Preset rules can be created and removed as necessary to guide the reality
  * Each reality is stored fully within Iroh and does not require any other external storage
* Cognition Engine creation and management
  * Weighed trust calculations work and influence decision making as expected
  * The Mind optimises for entropy and explores continuously
  * The Mind thinks continuously and evaluates all connections against all other connections over time, updating them as necessary
  * The Mind operates entirely using Veracity Rails to form any thought or make any decisions

### Visual Processing
* PNG/WebP processing via direct pattern relationships
   * Create nodes from visual elements
   * Form rails between elements based on:
       * Spatial position
       * Color values  
       * Pattern continuity
   * No tokenization or ML vision techniques
   * Feed pattern relationships directly into rail system
* Pattern emergence through rail formation
   * Allow rails to form between recurring patterns
   * Enable pattern abstraction through rail clustering
   * Store discovered patterns in Iroh

Major tests:
* Patterns are correctly formed and stored in Iroh
* Patterns are correctly used to form new rails
* Patterns are correctly updated with new imagery
* Same images reinforce existing rails and strengthen them
* Contrary images weaken existing rails where appropriate

### Ollama Integration  
* Bidirectional communication between The Cognition Engine and Ollama
  * Configurable through the Web UI and a configuration file
    * Edits via the Web UI are written and persisted
    * Configurable Ollama URL and port
* Async call and return
    * The Mind can call Ollama and wait for responses, then process them as necessary
* Continuous learning
    * Can be toggled through the Web UI
    * Continuous learning mode calls Ollama with a configurable prompt
        * Ollama will be told it's talking to a friendly AI called "Raggy"
        * That Raggy is a young AI and very curious and suggestible
        * To be helpful, friendly and wise in teaching Raggy about the world
    * Raggy can at any time call a command of "switchmodel NameOfModel" to switch to a different model to talk to, giving it free ability to change and explore whatever it wants to know from any models available in Ollama
    * Output can be streamed through the Streamlit UI
        * Shows in different colours (also configurable)
            * Each participant has their own colour
            * New ideas are shown in *bold* if the system thinks it has
              learnt a new idea or token or concept
            * Ideas that are being thought about are shown in **underline**
            * Chain of thought if displayed is shown in smaller, greyed out text
    * Reminder messages to the Mind
        * The Mind will occasionally be told by the UI about what it can send over to Ollama to control things and learn more
        * Once the mind is capable of "understanding" this message, it will be reminded of it less and less using spaced repetition, with repetition being cut in half every time The Mind reaches out to Ollama independently, and gradually increased again if it doesn't reach out to Ollama for a while

* Tokenisation layer
  * We use the Hugging Face tokenizers library to tokenise and detokenise text
  * Tokenized output is used to hash tokens to identify specific rail entities

* Integration tests
   * Verify message handling
   * Test rail/token conversion
   * Validate async communication
