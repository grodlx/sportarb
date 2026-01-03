import asyncio
import json
import aiohttp
from pathlib import Path

CLOB_API = "https://clob.polymarket.com/markets"

async def global_discovery():
    print("🌐 Querying CLOB for all live tradeable markets...")
    all_assets = {}
    next_cursor = ""
    
    async with aiohttp.ClientSession() as session:
        while True:
            url = f"{CLOB_API}?next_cursor={next_cursor}" if next_cursor else CLOB_API
            async with session.get(url) as resp:
                data = await resp.json()
                markets = data.get('data', [])
                
                for m in markets:
                    tokens = m.get('tokens', [])
                    if len(tokens) == 2:
                        # Extract the YES and NO IDs directly from the Order Book
                        ticker = m.get('question', 'Unknown')
                        all_assets[ticker] = {
                            "yes": tokens[0]['token_id'],
                            "no": tokens[1]['token_id']
                        }
                
                next_cursor = data.get('next_cursor', "")
                if not next_cursor or next_cursor == "none":
                    break
                    
        if all_assets:
            Path("assets.json").write_text(json.dumps(all_assets, indent=4))
            print(f"✅ Success! Found {len(all_assets)} live binary markets.")
        else:
            print("❌ No markets found. Ensure the API is accessible.")

if __name__ == "__main__":
    asyncio.run(global_discovery())
