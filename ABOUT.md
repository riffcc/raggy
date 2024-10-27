# Unbreakable rules
* All code must be written in Python3
* pip3 is the package manager, manage requirements.txt carefully
* Use pytest for testing
* Use black for formatting
* Use isort for sorting imports
* All new code must have 80% or greater test coverage
* All new code must have 80% or greater type checking coverage
* NEVER EVER mock code, always implement or stub. Do not make mocks. They do not help.

# Veracity rails
* Do not overload the veracity rail concept.
* Rails must be
  * Simple
  * Extremely lightweight and flexible
* Do not hardcode any particular "kind" of trust rail or entity
  * While we want it to be capable of semantic closeness as a form of a rail, we do not want that to be the only kind of rail. That's silly.

Veracity rails are a very simple construct, based on reputation, but are not directly a form of reputation.

A veracity rail is formed with the following process:

1. Create a document in Iroh representing the veracity rail
2. Create a ticket for writing to that document and store it in TicketWriteDoc for your node.
3. Create a ticket for reading from that document and store it in TicketReadDoc for your node.
4. For the entities you want to link together with the veracity rail, do the following:
  * Form metadata for the link as JSON or similar
  * Get the CID of the VeracityRailDoc
  * Store the VeracityRailDoc's CID into the entity's EntityDoc as a k/v in the form of key=cid, value=metadata

At the end of the process, both entities will be able to look up the VeracityRailDoc and use it to access the document and evaluate the rail.

# Progression rules
* Do NOT continue once you believe you've made a single test pass. Report success and allow us to test before you attempt new things. ALWAYS.