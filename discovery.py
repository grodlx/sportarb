import requests
import json

def fetch_sports_assets():
    print("🔍 Scanning Gamma API for Sports Asset IDs...")
    # Tag 100381 is often used for Sports, or we filter by category
    url = "https://gamma-api.polymarket.com/markets?active=true&limit=100"
    markets = requests.get(url).json()
    
    active_assets = {}
    for m in markets:
        # Filter for Sports and ensure it's a binary (Yes/No) market
        if "Sports" in str(m.get('tags')) or m.get('group_tag') == "Sports":
            try:
                ticker = m['ticker']
                # Polymarket CLOB uses 'clobTokenIds' for WebSockets
                clob_ids = json.loads(m['clobTokenIds']) 
                active_assets[ticker] = {
                    "yes": clob_ids[0],
                    "no": clob_ids[1]
                }
            except:
                continue
                
    with open("assets.json", "w") as f:
        json.dump(active_assets, f)
    print(f"✅ Saved {len(active_assets)} sports markets to assets.json")

if __name__ == "__main__":
    fetch_sports_assets()
