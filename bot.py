import asyncio
import json
import websockets
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()

class GlobalArbBot:
    def __init__(self, asset_map):
        self.asset_map = asset_map
        self.prices = {ticker: {"YES": 0.0, "NO": 0.0} for ticker in asset_map}
        self.id_to_market = {}
        self.pnl = 0.0

        for ticker, ids in asset_map.items():
            self.id_to_market[ids['yes']] = (ticker, "YES")
            self.id_to_market[ids['no']] = (ticker, "NO")

    async def run(self):
        uri = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
        async with websockets.connect(uri) as ws:
            subscribe_msg = {
                "type": "subscribe",
                "assets_ids": list(self.id_to_market.keys()),
                "channels": ["book"]
            }
            await ws.send(json.dumps(subscribe_msg))
            console.print(f"[bold cyan]🚀 MONITORING {len(self.asset_map)} MARKETS...[/bold cyan]")

            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                updates = data if isinstance(data, list) else [data]
                
                for update in updates:
                    if update.get("event_type") == "book":
                        asset_id = update.get("asset_id")
                        if asset_id in self.id_to_market:
                            ticker, side = self.id_to_market[asset_id]
                            if update.get("asks"):
                                self.prices[ticker][side] = float(update["asks"][0]["price"])
                                self.check_arb(ticker)

    def check_arb(self, ticker):
        p_yes = self.prices[ticker]["YES"]
        p_no = self.prices[ticker]["NO"]
        
        if p_yes > 0 and p_no > 0:
            total = p_yes + p_no
            if 0.10 < total < 0.999: # Arb Threshold
                profit = (1.0 - total) * 100 # Multiplier of 100
                self.pnl += profit
                console.print(f"[bold green]💰 ARB FOUND: {ticker[:30]}... | SUM: {total:.3f} | PnL: ${self.pnl:.2f}[/bold green]")

async def start():
    try:
        with open("assets.json", "r") as f:
            assets = json.load(f)
        bot = GlobalArbBot(assets)
        await bot.run()
    except FileNotFoundError:
        console.print("[red]Error: Please run discovery.py first.[/red]")

if __name__ == "__main__":
    asyncio.run(start())
