import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# User Settings
MULTIPLIER = 100 
CATEGORY = "Sports"
CHECK_INTERVAL = 15 

class PaperTrader:
    def __init__(self):
        self.balance = 1000.0 
        self.realized_pnl = 0.0

    def execute_trade(self, ticker, p_yes, p_no):
        shares = MULTIPLIER
        cost = (p_yes + p_no) * shares
        profit = (1.00 * shares) - cost
        self.realized_pnl += profit
        
        print(f"🚀 BUY: {ticker} | Price Sum: ${(p_yes + p_no):.3f}")
        print(f"   Positions: {shares} YES + {shares} NO")
        print(f"   Trade PnL: +${profit:.2f} | Total Realized PnL: ${self.realized_pnl:.2f}\n")

def get_sports_markets():
    url = "https://gamma-api.polymarket.com/markets?active=true&limit=100"
    try:
        resp = requests.get(url).json()
        # Filter for Sports and binary (Yes/No) markets
        return [m for m in resp if (m.get('group_tag') == CATEGORY) and len(m.get('outcomePrices', [])) == 2]
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return []

def main():
    trader = PaperTrader()
    print("--- Polymarket Arb Bot Started (Paper Trading) ---")
    
    while True:
        markets = get_sports_markets()
        for m in markets:
            p_yes = float(m['outcomePrices'][0])
            p_no = float(m['outcomePrices'][1])
            ticker = m.get('ticker', 'Unknown')
            
            if (p_yes + p_no) < 1.00:
                trader.execute_trade(ticker, p_yes, p_no)
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
