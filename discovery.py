import asyncio
import json
import aiohttp
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.status import Status

console = Console()
CLOB_API = "https://clob.polymarket.com/markets"

async def global_discovery():
    all_assets = {}
    next_cursor = ""
    
    # Visual 1: Initial Spinner
    with Status("[bold yellow]Connecting to Polymarket CLOB...", spinner="dots") as status:
        async with aiohttp.ClientSession() as session:
            
            # Visual 2: Progress Bar for Pagination
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                
                discovery_task = progress.add_task("[cyan]Fetching tradeable markets...", total=None)
                
                while True:
                    url = f"{CLOB_API}?next_cursor={next_cursor}" if next_cursor else CLOB_API
                    
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            console.print(f"[red]❌ API Error: {resp.status}[/red]")
                            break
                            
                        data = await resp.json()
                        markets = data.get('data', [])
                        
                        # Process batch
                        batch_count = 0
                        for m in markets:
                            tokens = m.get('tokens', [])
                            if len(tokens) == 2:
                                ticker = m.get('question', 'Unknown')
                                all_assets[ticker] = {
                                    "yes": tokens[0]['token_id'],
                                    "no": tokens[1]['token_id']
                                }
                                batch_count += 1
                        
                        # Update progress description with live count
                        progress.update(
                            discovery_task, 
                            description=f"[cyan]Found {len(all_assets)} binary markets..."
                        )
                        
                        next_cursor = data.get('next_cursor', "")
                        if not next_cursor or next_cursor == "none":
                            progress.update(discovery_task, completed=100, total=100)
                            break
                            
                        # Brief sleep to prevent rate limiting and keep UI smooth
                        await asyncio.sleep(0.1)

    if all_assets:
        Path("assets.json").write_text(json.dumps(all_assets, indent=4))
        console.print(f"\n[bold green]✅ Discovery Complete![/bold green]")
        console.print(f"📦 Total Assets Cached: [bold white]{len(all_assets)}[/bold white]")
        console.print(f"📂 Saved to: [blue]assets.json[/blue]\n")
    else:
        console.print("[bold red]❌ No markets found. Check your API access.[/bold red]")

if __name__ == "__main__":
    asyncio.run(global_discovery())
