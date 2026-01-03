import asyncio
import json
import websockets
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()

class HHFBot:
    def __init__(self, asset_map):
        self.asset_map = asset_map
        # Reverse map for quick lookup: {asset_id: (ticker, type)}
        self.id_to_market = {}
        for ticker, ids in asset_map.items():
            self.id_to_market[ids['yes']] = (ticker, "YES")
            self.id_to_market[ids['no']] = (ticker, "NO")
        
        self.prices = {ticker: {"YES": 0.0, "NO": 0.0} for ticker in asset_map}
        self.pnl = 0.0

    async def listen(self):
        uri = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
        async with websockets.connect(uri) as ws:
            # Subscribe to all sports assets
            all_ids = list(self.id_to_market.keys())
            subscribe_msg = {
                "type": "subscribe",
                "assets_ids": all_ids,
                "channels": ["book"]
            }
            await ws.send(json.dumps(subscribe_msg))

            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                
                if data.get("event_type") == "book":
                    asset_id = data.get("asset_id")
                    ticker, side = self.id_to_market[asset_id]
                    
                    # Get best ASK price (the price we buy at)
                    if data.get("asks"):
                        best_ask = float(data["asks"][0]["price"])
                        self.prices[ticker][side] = best_ask
                        self.check_arb(ticker)

    def check_arb(self, ticker):
        p_yes = self.prices[ticker]["YES"]
        p_no = self.prices[ticker]["NO"]
        
        if p_yes > 0 and p_no > 0:
            total = p_yes + p_no
            if total < 0.998:  # 0.2% margin for safety
                profit = (1.0 - total) * 100 # Using 100 multiplier
                self.pnl += profit
                console.print(f"[bold green]🔥 ARB DETECTED: {ticker} | Sum: {total:.3f} | +${profit:.2f}[/bold green]")

async def main():
    with open("assets.json", "r") as f:
        assets = json.load(f)
    
    bot = HHFBot(assets)
    await bot.listen()

if __name__ == "__main__":
    asyncio.run(main())
