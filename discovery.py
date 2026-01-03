import asyncio
import json
import aiohttp
from rich.console import Console

console = Console()
# Gamma for Human Metadata, CLOB for Trading IDs
GAMMA_URL = "https://gamma-api.polymarket.com/events"

async def pro_discovery():
    console.print("\n[bold blue]🛠 High-Frequency Asset Discovery Initializing...[/bold blue]")
    
    # Pro-tip: Filter by volume to avoid 'needle in haystack' dead markets
    params = {
        "active": "true",
        "closed": "false",
        "limit": "100",
        "order": "volume",
        "ascending": "false"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(GAMMA_URL, params=params) as resp:
            data = await resp.json()
            
            assets = {}
            for event in data:
                for market in event.get('markets', []):
                    # We ONLY want markets with CLOB IDs (tradeable)
                    token_ids_raw = market.get('clobTokenIds')
                    if token_ids_raw:
                        ids = json.loads(token_ids_raw) if isinstance(token_ids_raw, str) else token_ids_raw
                        # Binary Arb only works with exactly 2 outcomes (Yes/No)
                        if len(ids) == 2:
                            assets[market['ticker']] = {
                                "yes": ids[0],
                                "no": ids[1],
                                "vol": float(market.get('volume', 0))
                            }

            # Filter for liquidity: only watch markets with >$500 daily volume
            liquid_assets = {k: v for k, v in assets.items() if v['vol'] > 500}
            
            with open("assets.json", "w") as f:
                # Save just the IDs for the bot to run fast
                json.dump({k: {"yes": v["yes"], "no": v["no"]} for k, v in liquid_assets.items()}, f, indent=4)
                
            console.print(f"[bold green]✅ Success! Monitoring {len(liquid_assets)} high-liquidity markets.[/bold green]")

if __name__ == "__main__":
    asyncio.run(pro_discovery())
