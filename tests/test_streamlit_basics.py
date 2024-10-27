import pytest
import streamlit as st
from reality_engine.ui import create_app

async def test_streamlit_boots():
    app = await create_app()
    assert app is not None
    assert hasattr(st, "session_state")

async def test_streamlit_renders():
    app = await create_app()
    # Check main components are rendered
    assert "reality_engine" in st.session_state
    assert "main_view" in st.session_state
    assert st.session_state.get("blank_page", False) is False
