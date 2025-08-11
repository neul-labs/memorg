import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_mcp_import():
    """Test that the MCP server can be imported."""
    try:
        from app.mcp.server import MemorgMCP
        assert MemorgMCP is not None
    except ImportError as e:
        pytest.fail(f"Failed to import MemorgMCP: {e}")

def test_mcp_initialization():
    """Test that the MCP server can be initialized."""
    try:
        from app.mcp.server import MemorgMCP
        mcp = MemorgMCP()
        assert mcp is not None
        assert mcp.mcp is not None
    except Exception as e:
        pytest.fail(f"Failed to initialize MemorgMCP: {e}")