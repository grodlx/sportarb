import asyncio
import json
import aiohttp
from pathlib import Path
from rich.console import Console

console = Console()
CLOB_API = "https://clob.polymarket.com/markets"

async def smart_discovery():
    console.print("[bold yellow]🚀 Running High-Priority Discovery...[/bold yellow]")
    prioritized_assets = {}
    next_cursor = ""
    
    async with aiohttp.ClientSession() as session:
        while True:
            url = f"{CLOB_API}?next_cursor={next_cursor}" if next_cursor else CLOB_API
            async with session.get(url) as resp:
                data = await resp.json()
                markets = data.get('data', [])
                
                for m in markets:
                    # HEURISTIC 1: Must be binary
                    tokens = m.get('tokens', [])
                    if len(tokens) != 2: continue
                    
                    # HEURISTIC 2: Volume Check (Look for activity)
                    # We only care about markets people are actually trading
                    # 'volume' is usually provided in the CLOB market data
                    volume = float(m.get('volume', 0))
                    
                    # HEURISTIC 3: Filter out 'dust' markets
                    if volume < 500: continue # Adjust this based on your multiplier
                    
                    ticker = m.get('question', 'Unknown')
                    
                    # HEURISTIC 4: Keyword Prioritization (Sports/Current Events)
                    # These move faster and are more prone to retail-driven gaps
                    keywords = ["NBA", "NFL", "Winner", "Tournament", "Match"]
                    priority_boost = any(k in ticker for k in keywords)

                    if volume > 1000 or priority_boost:
                        prioritized_assets[ticker] = {
                            "yes": tokens[0]['token_id'],
                            "no": tokens[1]['token_id'],
                            "volume": volume
                        }

                next_cursor = data.get('next_cursor', "")
                if not next_cursor or next_cursor == "none" or len(prioritized_assets) > 500:
                    break
    
    Path("assets.json").write_text(json.dumps(prioritized_assets, indent=4))
    console.print(f"[bold green]✅ Success! Narrowed down to {len(prioritized_assets)} high-priority markets.[/bold green]")

if __name__ == "__main__":
    asyncio.run(smart_discovery())
