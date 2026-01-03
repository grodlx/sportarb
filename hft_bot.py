import asyncio
import json
import websockets
from rich.console import Console

console = Console()

class HHFBot:
    def __init__(self):
        self.prices = {}
        self.asset_map = {}
        self.id_to_market = {}
        self.pnl = 0.0

    def load_assets(self):
        with open("assets.json", "r") as f:
            self.asset_map = json.load(f)
        
        self.id_to_market = {}
        for ticker, ids in self.asset_map.items():
            self.id_to_market[ids['yes']] = (ticker, "YES")
            self.id_to_market[ids['no']] = (ticker, "NO")
            self.prices[ticker] = {"YES": 0.0, "NO": 0.0}

    async def listen(self):
        self.load_assets()
        uri = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
        
        async with websockets.connect(uri) as ws:
            subscribe_msg = {
                "type": "subscribe",
                "assets_ids": list(self.id_to_market.keys()),
                "channels": ["book"]
            }
            await ws.send(json.dumps(subscribe_msg))
            console.print("[yellow]Subscribed to WebSocket feeds...[/yellow]")

            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                
                # Filter for price updates
                if isinstance(data, list): data = data[0] # Handle occasional list responses
                
                if data.get("event_type") == "book":
                    asset_id = data.get("asset_id")
                    if asset_id in self.id_to_market:
                        ticker, side = self.id_to_market[asset_id]
                        if data.get("asks"):
                            # We only care about the cheapest price available to buy
                            self.prices[ticker][side] = float(data["asks"][0]["price"])
                            self.check_arb(ticker)

    def check_arb(self, ticker):
        p_yes = self.prices[ticker]["YES"]
        p_no = self.prices[ticker]["NO"]
        
        if p_yes > 0 and p_no > 0:
            total = p_yes + p_no
            if total < 0.999:
                profit = (1.0 - total) * 100 # Multiplier
                self.pnl += profit
                console.print(f"[bold green]💰 ARB: {ticker: <20} | Sum: {total:.3f} | Total PnL: ${self.pnl:.2f}[/bold green]")

async def main():
    bot = HHFBot()
    await bot.listen()

if __name__ == "__main__":
    asyncio.run(main())
