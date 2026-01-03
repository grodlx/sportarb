import asyncio
import json
import aiohttp
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
CLOB_API = "https://clob.polymarket.com/markets"

async def smart_discovery():
    console.print("\n[bold cyan]🔍 Global Market Discovery Initiated[/bold cyan]")
    all_discovered = []
    next_cursor = ""
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Broad Scan
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[yellow]Querying Polymarket Order Book...", total=None)
            
            while True:
                url = f"{CLOB_API}?next_cursor={next_cursor}" if next_cursor else CLOB_API
                async with session.get(url) as resp:
                    if resp.status != 200:
                        break
                    data = await resp.json()
                    markets = data.get('data', [])
                    
                    for m in markets:
                        tokens = m.get('tokens', [])
                        if len(tokens) == 2:
                            # Extracting stats
                            vol = float(m.get('volume', 0))
                            # Polymarket uses 'active' status in CLOB
                            if m.get('active'):
                                all_discovered.append({
                                    "ticker": m.get('question', 'Unknown'),
                                    "yes": tokens[0]['token_id'],
                                    "no": tokens[1]['token_id'],
                                    "volume": vol
                                })
                    
                    progress.update(task, description=f"[yellow]Scanned {len(all_discovered)} binary markets...")
                    next_cursor = data.get('next_cursor', "")
                    if not next_cursor or next_cursor == "none" or len(all_discovered) > 2000:
                        break

    # Step 2: Adaptive Filtering
    # We want markets with volume, but if there are none, we take the most recent ones.
    console.print(f"[bold green]✅ Scan Complete. Processing {len(all_discovered)} candidates...[/bold green]")
    
    # Sort by Volume descending
    all_discovered.sort(key=lambda x: x['volume'], reverse=True)
    
    # Filter for the "Hot List"
    # We take markets with volume > 100, OR just the top 100 markets if none have volume.
    hot_list = [m for m in all_discovered if m['volume'] > 100]
    
    if len(hot_list) < 20:
        console.print("[yellow]⚠️ Low volume markets detected. Falling back to Top 100 by activity.[/yellow]")
        hot_list = all_discovered[:100]

    # Step 3: Visual Confirmation Table
    table = Table(title="Selected High-Priority Markets")
    table.add_column("Market Question", style="magenta")
    table.add_column("24h Volume", justify="right", style="green")
    table.add_column("Status", justify="center")

    final_assets = {}
    for m in hot_list[:25]: # Show top 25 in terminal
        table.add_row(m['ticker'][:50] + "...", f"${m['volume']:,.2f}", "[cyan]WATCHING[/cyan]")
        final_assets[m['ticker']] = {"yes": m['yes'], "no": m['no']}

    # Save the full hot_list (up to 500) to JSON
    full_assets = {m['ticker']: {"yes": m['yes'], "no": m['no']} for m in hot_list}
    
    console.print(table)
    
    with open("assets.json", "w") as f:
        json.dump(full_assets, f, indent=4)
        
    console.print(f"\n[bold green]🚀 assets.json created with {len(full_assets)} priority markets![/bold green]")

if __name__ == "__main__":
    asyncio.run(smart_discovery())
