import iroh
import asyncio
import inspect

async def explore_authors():
    node = await iroh.Iroh.memory()
    authors = node.authors()
    
    # Print all available methods
    print("Available Authors methods:")
    for name, obj in inspect.getmembers(authors):
        if not name.startswith('_'):  # Skip private methods
            print(f"- {name}: {obj}")
    
    # Try to create an author
    try:
        author = await authors.create()
        print(f"\nCreated author: {author}")
        
        # Print author methods
        print("\nAuthor methods:")
        for name, obj in inspect.getmembers(author):
            if not name.startswith('_'):
                print(f"- {name}: {obj}")
                
    except Exception as e:
        print(f"Error creating author: {e}")

if __name__ == "__main__":
    asyncio.run(explore_authors())
