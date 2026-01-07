#!/usr/bin/env python3
"""
TradingView Pine Script Extractor.

Automatically extracts Pine Script source code from TradingView URLs.
Works with open-source scripts by intercepting the pine-facade API call.

Usage:
    python scripts/pinescript_extractor.py <url>
    python scripts/pinescript_extractor.py https://www.tradingview.com/script/tMtleB1G-Liqudation-HeatMap-BigBeluga/

Output:
    JSON with script metadata and source code to stdout.
    Errors go to stderr.

Requirements:
    - playwright (pip install playwright && playwright install chromium)
"""

import asyncio
import json
import re
import sys
from typing import cast

try:
    from playwright.async_api import async_playwright
except ImportError:
    print(
        "Error: playwright not installed. Run: pip install playwright && playwright install chromium",
        file=sys.stderr,
    )
    sys.exit(1)


async def extract_pinescript(url: str) -> dict:
    """
    Extract Pine Script source code from a TradingView script URL.

    Args:
        url: TradingView script URL (e.g., https://www.tradingview.com/script/ABC123-Name/)

    Returns:
        dict with keys:
            - success: bool
            - url: original URL
            - name: script name
            - source: Pine Script source code (if found)
            - metadata: additional metadata (author, version, etc.)
            - error: error message (if failed)
    """
    result = {
        "success": False,
        "url": url,
        "name": None,
        "source": None,
        "metadata": {},
        "error": None,
    }

    source_code = None
    api_data = None

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            page = await context.new_page()

            # Intercept network requests to catch the pine-facade API call
            async def handle_response(response):
                nonlocal source_code, api_data
                response_url = response.url

                # Look for the pine-facade API response
                if "pine-facade.tradingview.com/pine-facade/get/" in response_url:
                    try:
                        content_type = response.headers.get("content-type", "")
                        if "json" in content_type or "text" in content_type:
                            body = await response.text()
                            if "//@version" in body or "indicator(" in body or "strategy(" in body:
                                # Parse JSON response
                                try:
                                    data = json.loads(body)
                                    if isinstance(data, dict) and "source" in data:
                                        source_code = data["source"]
                                        api_data = data
                                        print(
                                            f"Found Pine Script via API: {response_url}",
                                            file=sys.stderr,
                                        )
                                except json.JSONDecodeError:
                                    # Not JSON, might be raw source
                                    source_code = body
                    except Exception as e:
                        print(f"Error processing response: {e}", file=sys.stderr)

            page.on("response", handle_response)

            print(f"Navigating to {url}...", file=sys.stderr)
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(2000)

            # Click Source code tab to trigger the API call
            try:
                btn = await page.query_selector('button:has-text("Source code")')
                if btn:
                    await btn.click()
                    print("Clicked Source code tab", file=sys.stderr)
                    await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Warning: Could not click Source code tab: {e}", file=sys.stderr)

            # Extract script name from page title
            title = await page.title()
            if title:
                # Parse title like "Liquidation HeatMap [BigBeluga] — Indicator by BigBeluga — TradingView"
                match = re.match(r"(.+?)\s*—", title)
                if match:
                    result["name"] = match.group(1).strip()

            # If API didn't capture source, try JavaScript evaluation
            if not source_code:
                code_content = await page.evaluate("""
                    () => {
                        // Try CodeMirror
                        const cm = document.querySelector('.CodeMirror');
                        if (cm && cm.CodeMirror) {
                            return cm.CodeMirror.getValue();
                        }

                        // Try Monaco editor
                        if (window.monaco && window.monaco.editor) {
                            const editors = window.monaco.editor.getEditors();
                            if (editors && editors.length > 0) {
                                return editors[0].getValue();
                            }
                        }

                        // Try pre/code elements with pine patterns
                        const pres = document.querySelectorAll('pre, code, .tv-script-src-code__code');
                        for (const pre of pres) {
                            const text = pre.textContent || pre.innerText;
                            if (text && (text.includes('//@version') || text.includes('indicator(') || text.includes('strategy('))) {
                                return text;
                            }
                        }

                        return null;
                    }
                """)
                if code_content:
                    source_code = code_content
                    print("Found code via JavaScript evaluation", file=sys.stderr)

            await browser.close()

        except Exception as e:
            result["error"] = str(e)
            return result

    if source_code:
        result["success"] = True
        result["source"] = source_code

        # Extract metadata from API response
        if api_data and isinstance(api_data, dict):
            result["metadata"] = {
                "created": api_data.get("created"),
                "updated": api_data.get("updated"),
                "version": api_data.get("version"),
                "script_name": api_data.get("scriptName"),
                "script_access": api_data.get("scriptAccess"),
            }
            extra = api_data.get("extra")
            if extra and isinstance(extra, dict):
                metadata = cast(dict, result["metadata"])
                metadata["kind"] = extra.get("kind")

        # Parse version from source if not in metadata
        metadata = cast(dict, result["metadata"])
        if not metadata.get("version"):
            version_match = re.search(r"//@version=(\d+)", source_code)
            if version_match:
                metadata["pine_version"] = int(version_match.group(1))

    else:
        result["error"] = (
            "Could not extract Pine Script source code. The script may be protected or invite-only."
        )

    return result


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python pinescript_extractor.py <tradingview_url>", file=sys.stderr)
        print(
            "Example: python pinescript_extractor.py https://www.tradingview.com/script/tMtleB1G-Liqudation-HeatMap-BigBeluga/",
            file=sys.stderr,
        )
        sys.exit(1)

    url = sys.argv[1]

    # Validate URL
    if "tradingview.com/script/" not in url:
        print(
            "Error: URL must be a TradingView script URL (e.g., https://www.tradingview.com/script/ABC123)",
            file=sys.stderr,
        )
        sys.exit(1)

    result = asyncio.run(extract_pinescript(url))

    # Output result as JSON
    print(json.dumps(result, indent=2))

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
