import asyncio
import json
import aiohttp
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()
# Use Gamma API for initial discovery to filter by 'closed' status
GAMMA_API = "https://gamma-api.polymarket.com/events"

async def live_discovery():
    console.print("\n[bold cyan]📡 Scanning for LIVE Tradeable Markets...[/bold cyan]")
    live_assets = {}
    
    # PARAMETERS: active=true and closed=false are MANDATORY to avoid 2023 data
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(GAMMA_API, params=params) as resp:
            if resp.status != 200:
                console.print(f"[red]Error: {resp.status}[/red]")
                return

            events = await resp.json()
            
            for event in events:
                # Each event (e.g. "Lakers vs Celtics") can have multiple markets
                for market in event.get('markets', []):
                    ticker = market.get('ticker')
                    clob_raw = market.get('clobTokenIds')
                    
                    if clob_raw and ticker:
                        # Only grab binary Yes/No markets
                        ids = json.loads(clob_raw) if isinstance(clob_raw, str) else clob_raw
                        if len(ids) == 2:
                            live_assets[ticker] = {
                                "yes": ids[0],
                                "no": ids[1],
                                "volume": float(market.get('volume', 0))
                            }

    # Display only the truly LIVE ones
    table = Table(title="Currently Active Polymarket Bets")
    table.add_column("Market Ticker", style="cyan")
    table.add_column("24h Vol", justify="right")
    
    for ticker, data in list(live_assets.items())[:20]:
        table.add_row(ticker[:50], f"${data['volume']:,.2f}")
    
    console.print(table)
    
    # Save for the bot
    with open("assets.json", "w") as f:
        # Format for bot.py
        bot_format = {k: {"yes": v["yes"], "no": v["no"]} for k, v in live_assets.items()}
        json.dump(bot_format, f, indent=4)
        
    console.print(f"\n[bold green]✅ Success! Cached {len(live_assets)} CURRENT markets.[/bold green]")

if __name__ == "__main__":
    asyncio.run(live_discovery())
