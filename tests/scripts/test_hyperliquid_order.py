#!/usr/bin/env python3
"""Test Hyperliquid testnet order placement and cancellation."""

import os

from dotenv import load_dotenv
from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

load_dotenv()


def main():
    print("=== Hyperliquid Testnet Order Test ===")
    print()

    # Setup
    pk = os.environ.get("HYPERLIQUID_TESTNET_PK")
    if not pk:
        print("ERROR: HYPERLIQUID_TESTNET_PK not set")
        return False

    account = Account.from_key(pk)
    address = account.address
    print(f"Wallet: {address[:10]}...{address[-6:]}")

    # Connect
    info = Info(constants.TESTNET_API_URL, skip_ws=True)
    exchange = Exchange(account, constants.TESTNET_API_URL)

    # Check balance
    user_state = info.user_state(address)
    margin = user_state.get("marginSummary", {})
    account_value = margin.get("accountValue", "0")
    print(f"Account Value: ${float(account_value):,.2f}")
    print()

    # Get BTC price
    all_mids = info.all_mids()
    btc_price = float(all_mids.get("BTC", 0))
    print(f"BTC Price: ${btc_price:,.2f}")

    # Place a small limit order (far from market - won't fill)
    limit_price = round(btc_price * 0.90, 1)  # 10% below market
    size = 0.001  # Minimum size

    print(f"Placing test order: BUY 0.001 BTC @ ${limit_price:,.1f} (10% below market)")
    print()

    result = exchange.order(
        coin="BTC",
        is_buy=True,
        sz=size,
        limit_px=limit_price,
        order_type={"limit": {"tif": "Gtc"}},
        reduce_only=False,
    )

    if result.get("status") == "ok":
        response = result.get("response", {})
        if response.get("type") == "order":
            order_data = response.get("data", {}).get("statuses", [{}])[0]
            if "resting" in order_data:
                oid = order_data["resting"]["oid"]
                print("✅ Order placed successfully!")
                print(f"   Order ID: {oid}")

                # Cancel it immediately
                cancel_result = exchange.cancel(coin="BTC", oid=oid)
                if cancel_result.get("status") == "ok":
                    print("✅ Order cancelled (cleanup)")
                else:
                    print(f"⚠️ Cancel failed: {cancel_result}")
                return True
            elif "filled" in order_data:
                print("⚠️ Order filled immediately (unexpected at this price)")
                return True
            else:
                print(f"Order status: {order_data}")
        else:
            print(f"Response: {response}")
    else:
        print(f"❌ Order failed: {result}")
        return False

    print()
    print("=== Test Complete ===")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
