#!/usr/bin/env python3
"""
Compass App MVP: Python Compass for Android (Termux)
Main Controller & Entry Point
"""

import argparse
import logging
import os
import sys
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("compass_app")

def parse_args():
    parser = argparse.ArgumentParser(description="Compass App MVP (Termux)")
    parser.add_argument(
        "--mode", 
        choices=["web", "cli", "both"], 
        default="web",
        help="UI mode (default: web)"
    )
    parser.add_argument(
        "--no-ui", 
        action="store_true", 
        help="Disable Web UI (same as --mode cli)"
    )
    parser.add_argument(
        "--mock", 
        action="store_true", 
        help="Use mock sensor data"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=int(os.environ.get("COMPASS_PORT", 8080)),
        help="Web UI port (default: 8080)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        
    if args.no_ui:
        args.mode = "cli"
        
    logger.info(f"Starting Compass App (Mode: {args.mode}, Mock: {args.mock})")
    
    # Фаза 1: Stub
    try:
        if args.mode in ["web", "both"]:
            logger.info(f"Web UI: http://localhost:{args.port}")
            # TODO: start_server(args.port)
            
        logger.info("Application initialized. Press Ctrl+C to stop.")
        
        # Основной цикл (stub)
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
