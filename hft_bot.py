import asyncio
import json
import os
import websockets
from rich.console import Console

console = Console()

class HHFBot:
    def __init__(self):
        self.prices = {}
        self.id_to_market = {}
        self.pnl = 0.0

    def load_assets(self):
        if not os.path.exists("assets.json"):
            console.print("[red]Error: assets.json not found! Run discovery.py first.[/red]")
            return False
        
        with open("assets.json", "r") as f:
            asset_map = json.load(f)
        
        if not asset_map:
            console.print("[red]Error: assets.json is empty![/red]")
            return False

        for ticker, ids in asset_map.items():
            self.id_to_market[ids['yes']] = (ticker, "YES")
            self.id_to_market[ids['no']] = (ticker, "NO")
            self.prices[ticker] = {"YES": 0.0, "NO": 0.0}
        return True

    async def listen(self):
        if not self.load_assets(): return

        uri = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
        async with websockets.connect(uri) as ws:
            # Subscribe to all discovered IDs
            subscribe_msg = {
                "type": "subscribe",
                "assets_ids": list(self.id_to_market.keys()),
                "channels": ["book"]
            }
            await ws.send(json.dumps(subscribe_msg))
            console.print(f"[green]Monitoring {len(self.prices)} sports markets...[/green]")

            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                
                # WebSocket sends a list or a dict depending on the event
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
            if 0.01 < total < 0.999: # Ignore 0.0 prices
                profit = (1.0 - total) * 100
                self.pnl += profit
                console.print(f"[bold green]💰 ARB: {ticker: <20} | Sum: {total:.3f} | PnL: ${self.pnl:.2f}[/bold green]")

async def main():
    bot = HHFBot()
    await bot.listen()

if __name__ == "__main__":
    asyncio.run(main())
