import time
import requests
from rich.console import Console
from rich.table import Table
from rich.live import Live

# Settings
MULTIPLIER = 100
CATEGORY = "Sports"
CHECK_INTERVAL = 5  # Faster refresh for the dashboard

console = Console()

class PaperTrader:
    def __init__(self):
        self.realized_pnl = 0.0
        self.trades_count = 0

    def record_trade(self, price_sum):
        profit = (1.00 - price_sum) * MULTIPLIER
        self.realized_pnl += profit
        self.trades_count += 1
        return profit

trader = PaperTrader()

def get_sports_data():
    url = "https://gamma-api.polymarket.com/markets?active=true&limit=50"
    try:
        resp = requests.get(url).json()
        # Filtering for Sports markets with exactly two outcomes (Yes/No)
        return [m for m in resp if (m.get('group_tag') == CATEGORY or 'Sports' in str(m.get('tags'))) 
                and len(m.get('outcomePrices', [])) == 2]
    except:
        return []

def generate_table():
    table = Table(title=f"Polymarket Sports Monitor (PnL: ${trader.realized_pnl:.2f})")
    table.add_column("Ticker", style="cyan")
    table.add_column("YES", justify="right")
    table.add_column("NO", justify="right")
    table.add_column("SUM", justify="right")
    table.add_column("Status", justify="center")

    markets = get_sports_data()
    
    for m in markets:
        try:
            p_yes = float(m['outcomePrices'][0])
            p_no = float(m['outcomePrices'][1])
            ticker = m.get('ticker', 'Unknown')[:20]
            price_sum = p_yes + p_no
            
            # Identify Arb
            if price_sum < 0.999: # Using 0.999 to account for float precision
                status = "[bold green]ARB FOUND[/bold green]"
                row_style = "on green"
                trader.record_trade(price_sum)
            else:
                status = "[red]NO ARB[/red]"
                row_style = ""

            table.add_row(
                ticker, 
                f"{p_yes:.3f}", 
                f"{p_no:.3f}", 
                f"{price_sum:.3f}", 
                status,
                style=row_style
            )
        except:
            continue
            
    return table

def run():
    with Live(generate_table(), refresh_per_second=1) as live:
        while True:
            time.sleep(CHECK_INTERVAL)
            live.update(generate_table())

if __name__ == "__main__":
    run()
