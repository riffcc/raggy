import pytest
from ..raggy_py.iroh import IrohNode

def test_create_main_doc():
    """Test if a node can create a MainDoc and keep it filled with necessary data."""
    node = IrohNode()
    main_doc = node.create_main_doc()
    assert main_doc is not None
    # Add more assertions to check if the MainDoc is filled with necessary data
