#!/usr/bin/env python3
"""
Memorg CLI entry point.
"""

import asyncio
import sys

def main():
    """Main entry point for the memorg CLI."""
    try:
        from memorg.cli import main as cli_main
        asyncio.run(cli_main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()