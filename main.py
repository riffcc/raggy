import iroh
import asyncio
import pytest

# TODO:
# * Iroh
#   * Docs
#     * Creating a doc
#     * Joining a doc
#     * Sharing a doc
#   * Nodes
#     * Creating a node
#     * Joining a node to a Defederation network
#
# * Entities
#   * Creating an entity
#   * Updating an entity
#   * Querying an entity
#
# * Veracity rails
#   * Creating a veracity rail
#     * Step-by step
#       * Ensure all entities have an Iroh document associated with them.
#       * Create a new Iroh document to represent the Veracity Rail and grab its CID.
#       * Add the CID to each entity's Iroh document
#         * with the key being the CID
#         * and the value being the strength of the relationship.
#       * Now you can look up the following information from either entity:
#         * Know that there exists a Veracity Rail
#         * Know the CID of the Veracity Rail
#         * Know the entities that are part of the Veracity Rail
#         * Know the strength of the relationship between each entity and the Veracity Rail
#   * Inference over veracity rails
#     * Step-by step
#       * Take the input sentence
#       * Split it into words with a tokenizer (the hugging face tokenizers library)
#       * Once tokenized, hash each token and create a CID from it.
#       * If the CID exists already, reuse it. If it does not, create one for it.
#       * Using the tokenizer or some other method, analyse the grammatical structure of the input.
#       * Send it to the entity trying to do the calculation of this inference.
#       * Now that we've got all the tokens and relationships for everything related to the tokens/the input:
#         * we can perform traditional inference steps over the Veracity Rails we've established.

# Inference in this system works on the following principles:
# * Entities can only influence other entities that they have a Veracity Rail to
# * The strength of the Veracity Rail determines the strength of the influence
# * Influence follows the Veracity Rails to the target entity
# * Entities can follow the Veracity Rails back to the source of the influence
# * This forms a weighted directed graph of influence
# * The strength of the influence determines how much weight is put on each connection
# * The end result is a weighted directed graph of influence
#
# Using traditional LLM methods blended with this new idea, we can create a new form of LLM - a Cognitive Language Model (CLM)
# It will learn by:
# * Receiving an input
# * Splitting it into tokens
# * Hashing each token to form a CID
# * Creating a Veracity Rail for each token
# * Using the input Veracity Rails to influence the output Veracity Rails
# * Using the output Veracity Rails to generate an output
# * Generating an output looks like:
#   * Taking the output Veracity Rails
#   * Using the influence values to form a weighted directed graph
#   * Walking the graph to the most entropic state
#   * Forming a sentence from the most entropic state
#
# This is a new kind of LLM - one that is not only queryable, but is also learnable.


async def main():
    try:
        # Create in memory iroh node
        node = await iroh.Iroh.memory()
        node_id = await node.net().node_id()
        print(f"Started Iroh node: {node_id}")

        # Create a document
        doc = await node.docs().create()
        print(f"Created doc: {doc.id()}")

        # Share the document to get read and write tickets
        read_ticket = await doc.share(iroh.ShareMode.READ, iroh.AddrInfoOptions.ID)
        print(f"Read-Access Ticket: {read_ticket}")

        write_ticket = await doc.share(iroh.ShareMode.WRITE, iroh.AddrInfoOptions.ID)
        print(f"Write-Access Ticket: {write_ticket}")

        # Example of joining a document using a ticket
        # Replace TICKET with a valid ticket string
        TICKET = iroh.DocTicket("docaaa7qg6afc6zupqzfxmu5uuueaoei5zlye7a4ahhrfhvzjfrfewozgybl5kkl6u6fqcnjxvdkoihq3nbsqczxeulfsqvatb2qh3bwheoyahacitior2ha4z2f4xxk43fgewtcltemvzhaltjojxwqltomv2ho33snmxc6biajjeteswek4ambkabzpcfoajganyabbz2zplaaaaaaaaaagrjyvlqcjqdoaaioowl2ygi2likyov62rofk4asma3qacdtvs6whqsdbizopsefrrkx")
        joined_doc = await node.docs().join(TICKET)
        print(f"Joined doc: {joined_doc.id()}")

    except iroh.iroh_ffi.IrohError as e:
        print(f"Encountered an Iroh error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

asyncio.run(main())

@pytest.fixture
async def iroh_node():
    # Setup
    node = await iroh.Iroh.memory()
    yield node
    # Teardown
    await node.shutdown()

@pytest.mark.asyncio
async def test_create_node(iroh_node):
    assert iroh_node is not None
    node_id = await iroh_node.net().node_id()
    assert node_id is not None

@pytest.mark.asyncio
async def test_create_document(iroh_node):
    try:
        doc = await iroh_node.docs().create()
        assert doc is not None
        assert doc.id() is not None
    except iroh.iroh_ffi.IrohError as e:
        pytest.fail(f"Failed to create document: {e}")

@pytest.mark.asyncio
async def test_share_document(iroh_node):
    try:
        doc = await iroh_node.docs().create()
        read_ticket = await doc.share(iroh.ShareMode.READ, iroh.AddrInfoOptions.ID)
        write_ticket = await doc.share(iroh.ShareMode.WRITE, iroh.AddrInfoOptions.ID)
        assert read_ticket is not None
        assert write_ticket is not None
    except iroh.iroh_ffi.IrohError as e:
        pytest.fail(f"Failed to share document: {e}")

@pytest.mark.asyncio
async def test_join_document():
    # Create two separate nodes
    node1 = await iroh.Iroh.memory()
    node2 = await iroh.Iroh.memory()
    
    try:
        # Create a document on node1
        doc = await node1.docs().create()
        # Share it to get a ticket
        ticket = await doc.share(iroh.ShareMode.READ, iroh.AddrInfoOptions.ID)
        
        # Join the document from node2 using the ticket
        joined_doc = await node2.docs().join(ticket)
        
        assert joined_doc is not None
        assert joined_doc.id() == doc.id()  # The document IDs should match
    finally:
        # Clean up
        await node1.shutdown()
        await node2.shutdown()
