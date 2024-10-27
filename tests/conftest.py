import pytest
import asyncio
import streamlit as st
from pathlib import Path

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_data_dir():
    return Path(__file__).parent / "test_data"

@pytest.fixture(autouse=True)
def mock_streamlit():
    # Mock streamlit session state
    if not hasattr(st, "session_state"):
        st.session_state = {}
    return st
