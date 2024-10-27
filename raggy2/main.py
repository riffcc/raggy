import streamlit.web.bootstrap as bootstrap
from raggy2.ui import render

def main():
    """Main entry point"""
    bootstrap.run(render, "", [], {})

if __name__ == "__main__":
    main()
