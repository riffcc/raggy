import iroh

class VeracityRails:
    def __init__(self, node):
        self.node = node

    async def create_rail(self, entity_a, entity_b, weight):
        # Create a shared document for the rail
        doc = await self.node.docs().create()
        # Add the rail information to the document
        await doc.put("entity_a", entity_a)
        await doc.put("entity_b", entity_b)
        await doc.put("weight", weight)
        return doc

    async def update_rail(self, doc, new_weight):
        # Update the weight of the rail
        await doc.put("weight", new_weight)

    async def get_rail_info(self, doc):
        # Retrieve rail information
        entity_a = await doc.get("entity_a")
        entity_b = await doc.get("entity_b")
        weight = await doc.get("weight")
        return entity_a, entity_b, weight
