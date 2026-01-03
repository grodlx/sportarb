import asyncio
import json
import aiohttp
from rich.console import Console
from rich.table import Table

console = Console()
# API Endpoints
GAMMA_API = "https://gamma-api.polymarket.com/events"

async def discovery():
    console.print("\n[bold cyan]📡 Scanning Polymarket for LIVE tradeable assets...[/bold cyan]")
    assets = {}
    
    # Critical Parameters for 2026 API
    params = {
        "active": "true",
        "closed": "false",
        "limit": "100",  # Limit must be a string for some aiohttp versions
        "order": "volume", # Prioritize high-volume/live markets
        "ascending": "false"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(GAMMA_API, params=params) as resp:
                if resp.status != 200:
                    console.print(f"[red]❌ API Error: {resp.status}[/red]")
                    return

                events = await resp.json()
                
                for event in events:
                    # Filter for sports or general binary markets
                    # Events contain a 'markets' list
                    for market in event.get('markets', []):
                        ticker = market.get('ticker')
                        # The CLOB IDs are what we need for Hyper-Frequency
                        token_ids_raw = market.get('clobTokenIds')
                        
                        if token_ids_raw and ticker:
                            # Handle different data types for clobTokenIds
                            token_ids = json.loads(token_ids_raw) if isinstance(token_ids_raw, str) else token_ids_raw
                            
                            # Only accept binary YES/NO markets
                            if len(token_ids) == 2:
                                assets[ticker] = {
                                    "yes": token_ids[0],
                                    "no": token_ids[1],
                                    "volume": float(market.get('volume', 0))
                                }

        except Exception as e:
            console.print(f"[red]❌ Discovery Failed: {e}[/red]")
            return

    # Visualizing the results
    if assets:
        table = Table(title="Found Active Tradeable Markets")
        table.add_column("Ticker", style="cyan")
        table.add_column("24h Volume", justify="right", style="green")

        # Sort by volume to show the most "live" ones first
        sorted_assets = sorted(assets.items(), key=lambda x: x[1]['volume'], reverse=True)
        
        for ticker, data in sorted_assets[:20]: # Show top 20
            table.add_row(ticker[:50], f"${data['volume']:,.2f}")
        
        console.print(table)
        
        # Save formatted for the bot
        bot_config = {k: {"yes": v["yes"], "no": v["no"]} for k, v in assets.items()}
        with open("assets.json", "w") as f:
            json.dump(bot_config, f, indent=4)
            
        console.print(f"[bold green]✅ Success! Saved {len(assets)} live markets to assets.json[/bold green]")
    else:
        console.print("[bold red]⚠️ No active markets found. Ensure the API isn't rate-limiting you.[/bold red]")

if __name__ == "__main__":
    asyncio.run(discovery())
