import streamlit as st
from typing import Optional
from .core import Raggy

class RaggyUI:
    def __init__(self, raggy: Optional[Raggy] = None):
        self.raggy = raggy
        if 'initialized' not in st.session_state:
            st.session_state.initialized = False
            st.session_state.main_view = True
            st.session_state.blank_page = False
            
    async def initialize(self):
        if not self.raggy:
            self.raggy = await Raggy.create()
        st.session_state.initialized = True
        
    def render(self):
        if not st.session_state.initialized:
            st.error("UI not initialized")
            return
            
        st.title("Raggy")
        
        # Main navigation
        tabs = st.tabs(["Mind", "Reality", "Veracity"])
        
        with tabs[0]:
            self._render_mind_tab()
            
        with tabs[1]:
            self._render_reality_tab()
            
        with tabs[2]:
            self._render_veracity_tab()
    
    def _render_mind_tab(self):
        st.header("The Mind")
        st.text("Current thoughts and processing will appear here")
        
    def _render_reality_tab(self):
        st.header("Reality Layer")
        st.text("Reality simulation controls and visualization will appear here")
        
    def _render_veracity_tab(self):
        st.header("Veracity Rails")
        st.text("Trust and relationship visualization will appear here")

def create_ui() -> RaggyUI:
    return RaggyUI()
