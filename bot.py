import asyncio
import json
import websockets
from rich.live import Live
from rich.table import Table

# Settings inspired by poly-maker-bot
REFRESH_RATE = 0.1  # 100ms UI refresh
WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

class ArbitrageEngine:
    def __init__(self, assets):
        self.assets = assets
        self.prices = {ticker: {"YES": 0.0, "NO": 0.0} for ticker in assets}
        self.id_map = {}
        for ticker, ids in assets.items():
            self.id_map[ids['yes']] = (ticker, "YES")
            self.id_map[ids['no']] = (ticker, "NO")

    def generate_ui(self):
        table = Table(title="🔥 Real-Time Arbitrage Scanner")
        table.add_column("Market")
        table.add_column("Yes", justify="right")
        table.add_column("No", justify="right")
        table.add_column("Sum", justify="right", style="bold")
        
        for ticker, p in list(self.prices.items())[:15]: # Show top 15
            total = p["YES"] + p["NO"]
            sum_style = "green" if 0.1 < total < 0.995 else "white"
            table.add_row(ticker[:30], f"{p['YES']:.3f}", f"{p['NO']:.3f}", f"[{sum_style}]{total:.3f}[/]")
        return table

    async def start(self):
        async with websockets.connect(WS_URL) as ws:
            # Subscribe to all IDs at once (WebSocket limit is high)
            sub_msg = {"type": "subscribe", "assets_ids": list(self.id_map.keys()), "channels": ["book"]}
            await ws.send(json.dumps(sub_msg))

            with Live(self.generate_ui(), refresh_per_second=10) as live:
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    
                    # Handle price updates
                    if isinstance(data, list): data = data[0]
                    if data.get("event_type") == "book":
                        asset_id = data.get("asset_id")
                        if asset_id in self.id_map:
                            ticker, side = self.id_to_market[asset_id]
                            if data.get("asks"):
                                self.prices[ticker][side] = float(data["asks"][0]["price"])
                    
                    live.update(self.generate_ui())

# ... Boilerplate to load assets.json and run asyncio ...
