import asyncio
import json
import websockets
from rich.console import Console

console = Console()

class GlobalArbBot:
    def __init__(self):
        self.prices = {}
        self.id_to_market = {}
        self.pnl = 0.0

    def load_all_assets(self):
        with open("assets.json", "r") as f:
            assets = json.load(f)
        for ticker, ids in assets.items():
            self.id_to_market[ids['yes']] = (ticker, "YES")
            self.id_to_market[ids['no']] = (ticker, "NO")
            self.prices[ticker] = {"YES": 0.0, "NO": 0.0}
        return list(self.id_to_market.keys())

    async def start_streaming(self):
        all_ids = self.load_all_assets()
        uri = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
        
        async with websockets.connect(uri) as ws:
            # Subscribe to EVERYTHING found in discovery
            subscribe_msg = {
                "type": "subscribe",
                "assets_ids": all_ids,
                "channels": ["book"]
            }
            await ws.send(json.dumps(subscribe_msg))
            console.print(f"[bold cyan]🔥 MONITORING {len(self.prices)} GLOBAL MARKETS IN REAL-TIME...[/bold cyan]")

            while True:
                message = await ws.recv()
                data = json.loads(message)
                
                # WebSocket can return a single dict or a list of updates
                updates = data if isinstance(data, list) else [data]
                
                for update in updates:
                    if update.get("event_type") == "book":
                        asset_id = update.get("asset_id")
                        if asset_id in self.id_to_market:
                            ticker, side = self.id_to_market[asset_id]
                            # 'asks' [0] is the current best price to BUY that share
                            if update.get("asks"):
                                self.prices[ticker][side] = float(update["asks"][0]["price"])
                                self.calculate_arb(ticker)

    def calculate_arb(self, ticker):
        p_yes = self.prices[ticker]["YES"]
        p_no = self.prices[ticker]["NO"]
        
        if p_yes > 0 and p_no > 0:
            total_cost = p_yes + p_no
            # We check if the sum is below $1.00
            if 0.10 < total_cost < 0.999: # 0.10 floor filters out 'dead' markets
                profit = (1.0 - total_cost) * 100 # Multiplier of 100
                self.pnl += profit
                console.print(f"[bold green]💰 ARB FOUND! {ticker: <25} | SUM: {total_cost:.3f} | Total Paper PnL: ${self.pnl:.2f}[/bold green]")

async def main():
    bot = GlobalArbBot()
    await bot.start_streaming()

if __name__ == "__main__":
    asyncio.run(main())
