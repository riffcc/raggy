import pytest
import streamlit as st
from raggy.ui import RaggyUI, create_ui

async def test_streamlit_boots():
    """Test that Streamlit UI can be created and initialized"""
    ui = create_ui()
    assert ui is not None
    assert isinstance(ui, RaggyUI)
    
    # Test initialization
    await ui.initialize()
    assert st.session_state.initialized is True
    assert hasattr(st.session_state, 'main_view')
    assert hasattr(st.session_state, 'blank_page')

async def test_streamlit_renders():
    """Test that Streamlit UI renders all required components"""
    ui = create_ui()
    await ui.initialize()
    
    # Render the UI
    ui.render()
    
    # Verify session state
    assert st.session_state.initialized is True
    assert st.session_state.main_view is True
    assert st.session_state.blank_page is False
    
    # Basic structure tests
    # Note: We can't test actual rendering since Streamlit runs in its own process
    # But we can verify the UI object is properly configured
    assert hasattr(ui, '_render_mind_tab')
    assert hasattr(ui, '_render_reality_tab')
    assert hasattr(ui, '_render_veracity_tab')

async def test_streamlit_tabs():
    """Test that all required tabs are available"""
    ui = create_ui()
    await ui.initialize()
    
    # Render UI
    ui.render()
    
    # Verify tab methods exist and can be called
    ui._render_mind_tab()
    ui._render_reality_tab()
    ui._render_veracity_tab()
