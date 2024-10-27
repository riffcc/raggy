import iroh
import asyncio

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
