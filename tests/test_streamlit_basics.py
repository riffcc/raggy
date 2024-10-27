import pytest
import streamlit as st
from raggy.ui import create_ui

async def test_streamlit_boots():
    ui = await create_ui()
    assert ui is not None
    assert hasattr(st, "session_state")

async def test_streamlit_renders():
    ui = await create_ui()
    # Check main components are rendered
    assert "raggy" in st.session_state
    assert "main_view" in st.session_state
    assert st.session_state.get("blank_page", False) is False
