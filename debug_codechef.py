"""
Run this standalone to see exactly what CodeChef's API returns on your machine.
Usage: python debug_codechef.py

This helps diagnose which JSON structure/endpoint is live so codechef.py
can be updated to match it.
"""

import asyncio
import json
import aiohttp

ENDPOINTS = [
    "https://www.codechef.com/api/list/contests/future",
    "https://www.codechef.com/api/contests/?sort_by=start&sorting_order=asc&offset=0&mode=future",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; cp-notifier-bot/1.0)",
    "Accept": "application/json",
}


async def probe():
    async with aiohttp.ClientSession() as session:
        for url in ENDPOINTS:
            print(f"\n{'='*60}")
            print(f"URL: {url}")
            try:
                async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    print(f"Status: {resp.status}")
                    text = await resp.text()
                    try:
                        data = json.loads(text)
                        # Print top-level structure
                        if isinstance(data, dict):
                            print(f"Top-level keys: {list(data.keys())}")
                            # Try to find a list anywhere in the first 2 levels
                            for k, v in data.items():
                                if isinstance(v, list):
                                    print(f"  data['{k}'] is a list of {len(v)} items")
                                    if v:
                                        print(f"  First item keys: {list(v[0].keys()) if isinstance(v[0], dict) else type(v[0]).__name__}")
                                elif isinstance(v, dict):
                                    print(f"  data['{k}'] is a dict with keys: {list(v.keys())}")
                        elif isinstance(data, list):
                            print(f"Top level is a list of {len(data)} items")
                            if data:
                                print(f"First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else data[0]}")
                        # Print first 800 chars of raw JSON
                        print(f"\nRaw (first 800 chars):\n{text[:800]}")
                    except json.JSONDecodeError:
                        print(f"Not JSON. Raw response:\n{text[:400]}")
            except Exception as e:
                print(f"Error: {e}")

asyncio.run(probe())
