"""Command-line interface entry point for AXIOM."""

import argparse
import logging
import asyncio
from .repl import REPL

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="AXIOM Virtual Assistant Console")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    repl = REPL()
    asyncio.run(repl.run())

if __name__ == "__main__":
    main()
