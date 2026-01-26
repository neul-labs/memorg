import pytest

def test_mcp_import():
    """Test that the MCP server can be imported."""
    try:
        from memorg.mcp.server import MemorgMCP
        assert MemorgMCP is not None
    except ImportError as e:
        pytest.fail(f"Failed to import MemorgMCP: {e}")

def test_mcp_initialization():
    """Test that the MCP server can be initialized."""
    try:
        from memorg.mcp.server import MemorgMCP
        mcp = MemorgMCP()
        assert mcp is not None
        assert mcp.mcp is not None
    except Exception as e:
        pytest.fail(f"Failed to initialize MemorgMCP: {e}")