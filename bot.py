import asyncio
import json
import websockets
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from datetime import datetime

# --- Configuration ---
MULTIPLIER = 100
MIN_PROFIT_THRESHOLD = 0.005 # 0.5% profit min
MAX_WATCHLIST_SIZE = 50       # Keep it focused on the hottest assets
WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

console = Console()

class ArbDashboard:
    def __init__(self):
        self.prices = {}       # {ticker: {"YES": price, "NO": price}}
        self.stats = {"processed": 0, "arbs_found": 0, "pnl": 0.0}
        self.logs = []         # Recent arb alerts
        self.watchlist = {}    # {asset_id: (ticker, side)}

    def update_price(self, ticker, side, price):
        if ticker not in self.prices:
            self.prices[ticker] = {"YES": 0.0, "NO": 0.0}
        self.prices[ticker][side] = price
        self.stats["processed"] += 1

    def log_arb(self, ticker, sum_val):
        profit = (1.0 - sum_val) * MULTIPLIER
        self.stats["arbs_found"] += 1
        self.stats["pnl"] += profit
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] {ticker[:20]}.. | SUM: {sum_val:.3f} | +${profit:.2f}"
        self.logs = [entry] + self.logs[:5]

    def generate_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=8)
        )
        
        # Header: Stats
        stats_info = f"[bold cyan]Markets Processed:[/] {self.stats['processed']}  |  [bold green]Arbs Found:[/] {self.stats['arbs_found']}  |  [bold gold1]Total Paper PnL:[/] ${self.stats['pnl']:.2f}"
        layout["header"].update(Panel(stats_info, title="Polymarket HHF Arb Bot Status", border_style="blue"))

        # Main: Hot Watchlist
        table = Table(title="Live Hot-List Monitor", expand=True)
        table.add_column("Ticker", style="cyan", no_wrap=True)
        table.add_column("YES Ask", justify="right")
        table.add_column("NO Ask", justify="right")
        table.add_column("Sum", justify="right")
        table.add_column("Status", justify="center")

        # Display top 10 tickers with highest activity
        for ticker, p in list(self.prices.items())[:12]:
            s = p["YES"] + p["NO"]
            status = "[bold green]ARB![/]" if 0.1 < s < 0.999 else "[grey50]Monitoring[/]"
            table.add_row(ticker[:35], f"{p['YES']:.3f}", f"{p['NO']:.3f}", f"{s:.3f}", status)
        
        layout["main"].update(table)

        # Footer: Recent Executions
        log_content = "\n".join(self.logs) if self.logs else "Waiting for signals..."
        layout["footer"].update(Panel(log_content, title="Recent Arbitrage Executions", border_style="green"))
        
        return layout

async def run_bot():
    # Load assets from discovery
    with open("assets.json", "r") as f:
        assets = json.load(f)

    db = ArbDashboard()
    # Initial subscription to the first X assets (Discovery should have sorted them by volume)
    hot_assets = list(assets.items())[:MAX_WATCHLIST_SIZE]
    
    # Map for WebSocket lookup
    id_map = {}
    for ticker, ids in hot_assets:
        id_map[ids['yes']] = (ticker, "YES")
        id_map[ids['no']] = (ticker, "NO")

    async with websockets.connect(WS_URL) as ws:
        # Subscribe to hot assets
        sub_msg = {"type": "subscribe", "assets_ids": list(id_map.keys()), "channels": ["book"]}
        await ws.send(json.dumps(sub_msg))

        with Live(db.generate_layout(), refresh_per_second=4, screen=True) as live:
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                    
                    # Handle batch or single updates
                    updates = data if isinstance(data, list) else [data]
                    for up in updates:
                        if up.get("event_type") == "book":
                            aid = up.get("asset_id")
                            if aid in id_map:
                                ticker, side = id_map[aid]
                                if up.get("asks"):
                                    price = float(up["asks"][0]["price"])
                                    db.update_price(ticker, side, price)
                                    
                                    # Check Arb logic
                                    p = db.prices[ticker]
                                    if p["YES"] > 0 and p["NO"] > 0:
                                        s = p["YES"] + p["NO"]
                                        if 0.1 < s < (1.0 - MIN_PROFIT_THRESHOLD):
                                            db.log_arb(ticker, s)
                    
                    live.update(db.generate_layout())
                except asyncio.TimeoutError:
                    # Send Ping to keep connection alive
                    await ws.send(json.dumps({"type": "ping"}))
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    break

if __name__ == "__main__":
    asyncio.run(run_bot())
