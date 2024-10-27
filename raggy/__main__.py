import asyncio
import streamlit as st
from .ui import create_ui

async def main():
    ui = create_ui()
    await ui.initialize()
    ui.render()

if __name__ == "__main__":
    asyncio.run(main())
