"""Command-line interface entry point for AXIOM."""

import argparse
import asyncio
from pathlib import Path
from .repl import REPL
from axiom.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="AXIOM Virtual Assistant Console")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--log-dir", type=Path, help="Directory for log files (default: logs/)")
    args = parser.parse_args()
    
    # Initialize structured logging
    setup_logging(log_dir=args.log_dir, debug=args.debug)
    
    logger.info("Starting AXIOM Console", debug_mode=args.debug)
    
    try:
        repl = REPL()
        asyncio.run(repl.run())
    except Exception as e:
        logger.critical("Fatal error in AXIOM Console", error=str(e))
        raise

if __name__ == "__main__":
    main()
