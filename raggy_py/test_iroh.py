import pytest
from raggy_py.iroh import IrohNode

def test_create_main_doc():
    node = IrohNode()
    main_doc = node.create_main_doc()
    assert isinstance(main_doc, dict), "MainDoc should be a dictionary"
    assert main_doc == {}, "MainDoc should be initially empty"
