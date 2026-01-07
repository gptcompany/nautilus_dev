#!/usr/bin/env python3
"""Production live trading launcher for Hyperliquid (Spec 021 - Phase 8).

This script launches a production TradingNode for Hyperliquid with:
- Environment variable validation
- Graceful shutdown handling
- Configurable logging

IMPORTANT: For production use only after thorough testnet validation.

Environment Variables Required:
    HYPERLIQUID_PK: Private key for mainnet trading (production)
    HYPERLIQUID_TESTNET_PK: Private key for testnet trading (if --testnet)

Usage:
    python scripts/hyperliquid/run_live.py --strategy my_strategy.py

Example:
    # Run on testnet first
    python scripts/hyperliquid/run_live.py --testnet --strategy my_strategy.py

    # Run on mainnet (CAUTION!)
    python scripts/hyperliquid/run_live.py --strategy my_strategy.py
"""

import argparse
import os
import signal
import sys
from datetime import datetime

from nautilus_trader.common.enums import LogLevel
from nautilus_trader.config import LoggingConfig
from nautilus_trader.live.node import TradingNode


from configs.hyperliquid.trading_node import create_hyperliquid_trading_node


def validate_environment(testnet: bool) -> bool:
    """Validate required environment variables are set.

    Args:
        testnet: If True, check for testnet credentials.

    Returns:
        True if all required variables are set, False otherwise.
    """
    if testnet:
        env_var = "HYPERLIQUID_TESTNET_PK"
    else:
        env_var = "HYPERLIQUID_PK"

    if not os.environ.get(env_var):
        print(f"ERROR: {env_var} environment variable not set")
        print(f"Set it with: export {env_var}='0x...'")
        return False

    # Verify private key is not in source code (basic check)
    pk = os.environ.get(env_var, "")
    if len(pk) < 60:  # Valid private key should be ~66 chars
        print(f"WARNING: {env_var} appears to be invalid (too short)")
        return False

    return True


def setup_signal_handlers(node: TradingNode) -> None:
    """Setup graceful shutdown signal handlers.

    Args:
        node: The TradingNode to shutdown gracefully.
    """

    def signal_handler(signum, frame):
        signame = signal.Signals(signum).name
        print(f"\n[{datetime.now()}] Received {signame}, initiating graceful shutdown...")

        try:
            node.stop()
            print(f"[{datetime.now()}] Graceful shutdown complete")
        except Exception as e:
            print(f"[{datetime.now()}] Error during shutdown: {e}")
        finally:
            sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Run the live trading launcher."""
    parser = argparse.ArgumentParser(description="Launch production Hyperliquid trading node")
    parser.add_argument(
        "--testnet",
        action="store_true",
        help="Use testnet instead of mainnet (recommended for testing)",
    )
    parser.add_argument(
        "--trader-id",
        type=str,
        default="TRADER-HL-LIVE",
        help="Unique trader ID (default: TRADER-HL-LIVE)",
    )
    parser.add_argument(
        "--instruments",
        nargs="+",
        default=None,
        help="Instruments to trade (default: BTC-USD-PERP, ETH-USD-PERP)",
    )
    parser.add_argument(
        "--no-redis",
        action="store_true",
        help="Disable Redis caching",
    )
    parser.add_argument(
        "--redis-host",
        type=str,
        default="localhost",
        help="Redis host (default: localhost)",
    )
    parser.add_argument(
        "--redis-port",
        type=int,
        default=6379,
        help="Redis port (default: 6379)",
    )
    parser.add_argument(
        "--no-reconciliation",
        action="store_true",
        help="Disable position reconciliation on startup",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    args = parser.parse_args()

    # Validate environment
    if not validate_environment(args.testnet):
        sys.exit(1)

    # Print configuration
    print(f"[{datetime.now()}] Starting Hyperliquid Live Trading Node")
    print(f"  Mode: {'TESTNET' if args.testnet else 'MAINNET (PRODUCTION!)'}")
    print(f"  Trader ID: {args.trader_id}")
    print(f"  Instruments: {args.instruments or 'DEFAULT'}")
    print(f"  Redis: {'disabled' if args.no_redis else f'{args.redis_host}:{args.redis_port}'}")
    print(f"  Reconciliation: {'disabled' if args.no_reconciliation else 'enabled'}")
    print(f"  Log level: {args.log_level}")

    if not args.testnet:
        print("\n⚠️  WARNING: MAINNET MODE - Real funds at risk!")
        print("    Press Ctrl+C within 5 seconds to abort...")
        import time

        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nAborted by user")
            sys.exit(0)

    # Create base configuration
    base_config = create_hyperliquid_trading_node(
        trader_id=args.trader_id,
        testnet=args.testnet,
        instruments=args.instruments,
        redis_enabled=not args.no_redis,
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        reconciliation=not args.no_reconciliation,
    )

    # Create logging configuration
    log_level = getattr(LogLevel, args.log_level)
    logging_config = LoggingConfig(log_level=log_level)

    # Reconstruct config with logging (TradingNodeConfig is frozen)
    from nautilus_trader.config import TradingNodeConfig

    config = TradingNodeConfig(
        trader_id=base_config.trader_id,
        data_clients=base_config.data_clients,
        exec_clients=base_config.exec_clients,
        cache=base_config.cache,
        exec_engine=base_config.exec_engine,
        logging=logging_config,
    )

    # Create node
    node = TradingNode(config=config)

    # Setup signal handlers for graceful shutdown
    setup_signal_handlers(node)

    print(f"\n[{datetime.now()}] Node configured, starting...")
    print("  Add strategies before running in production!")
    print("  Press Ctrl+C for graceful shutdown")
    print()

    # Run node
    try:
        node.run()
    except Exception as e:
        print(f"\n[{datetime.now()}] Error: {e}")
        sys.exit(1)
    finally:
        print(f"[{datetime.now()}] Trading node stopped")


if __name__ == "__main__":
    main()
