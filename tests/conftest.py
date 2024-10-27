import pytest
import asyncio
import streamlit as st
from pathlib import Path

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_data_dir():
    """Provide a Path object pointing to the test data directory."""
    return Path(__file__).parent / "test_data"

@pytest.fixture(autouse=True)
def mock_streamlit():
    """Mock Streamlit session state for testing."""
    if not hasattr(st, "session_state"):
        st.session_state = {}
    st.session_state.raggy = True
    st.session_state.main_view = True
    st.session_state.blank_page = False
    return st

@pytest.fixture(autouse=True)
async def setup_iroh():
    """Setup and teardown Iroh for each test."""
    # Nothing to do for setup since each test creates its own node
    yield
    # Cleanup any remaining Iroh processes
    await asyncio.sleep(0.1)  # Allow time for cleanup
