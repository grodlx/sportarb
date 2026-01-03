import asyncio
import json
import aiohttp
from pathlib import Path

GAMMA_API = "https://gamma-api.polymarket.com"
# Tag 100381 = General Sports, Tag 100639 = Specific Games
TAG_IDS = ["100381", "100639"] 
CACHE_FILE = "assets.json"
CONCURRENT_REQUESTS = 5

async def fetch_page(session, tag_id, offset):
    params = {"tag_id": tag_id, "active": "true", "closed": "false", "limit": 100, "offset": offset}
    async with session.get(f"{GAMMA_API}/events", params=params) as resp:
        if resp.status == 200:
            return await resp.json()
        return []

async def main():
    active_assets = {}
    async with aiohttp.ClientSession() as session:
        for tag in TAG_IDS:
            print(f"🔍 Scanning Tag: {tag}")
            # Fetch first page to start
            events = await fetch_page(session, tag, 0)
            
            # Parallel fetch for offsets 100, 200, 300...
            tasks = [fetch_page(session, tag, i) for i in range(100, 1000, 100)]
            results = await asyncio.gather(*tasks)
            
            for page in [events] + list(results):
                for event in page:
                    for market in event.get("markets", []):
                        ticker = market.get("ticker")
                        clob_raw = market.get("clobTokenIds")
                        if clob_raw and ticker:
                            ids = json.loads(clob_raw) if isinstance(clob_raw, str) else clob_raw
                            if len(ids) == 2:
                                active_assets[ticker] = {"yes": ids[0], "no": ids[1]}

    Path(CACHE_FILE).write_text(json.dumps(active_assets, indent=4))
    print(f"✅ Cached {len(active_assets)} binary markets to {CACHE_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
