#!/usr/bin/env python3
"""
CLI entry point for the Memorg MCP server.
"""
import sys
import argparse
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.insert(0, '.')

from app.mcp.server import MemorgMCP

def main():
    \"\"\"Main entry point for the Memorg MCP server CLI.\"\"\"
    parser = argparse.ArgumentParser(description="Memorg MCP Server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to bind the server to (default: 3000)"
    )
    parser.add_argument(
        "--db-path",
        default="memorg.db",
        help="Path to the database file (default: memorg.db)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run the MCP server
    mcp_server = MemorgMCP(db_path=args.db_path)
    
    print(f"Starting Memorg MCP server on {args.host}:{args.port}")
    print(f"Database path: {args.db_path}")
    print(f"Log level: {args.log_level}")
    
    try:
        mcp_server.run(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nShutting down Memorg MCP server...")
    except Exception as e:
        print(f"Error running Memorg MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
