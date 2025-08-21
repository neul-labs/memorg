#!/usr/bin/env python3
"""
Memorg CLI entry point.
"""

import asyncio
import sys
import os

# Add the parent directory to sys.path to allow importing app.cli
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Main entry point for the memorg CLI."""
    try:
        # Import here to avoid issues with path manipulation
        from app.cli import main as cli_main
        asyncio.run(cli_main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()