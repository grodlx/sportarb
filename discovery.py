import requests
import json

def fetch_all_binary_assets():
    print("🔍 Scanning ALL Polymarket binary markets (Global Discovery)...")
    
    # Large limit to capture all active events
    url = "https://gamma-api.polymarket.com/events?limit=500&active=true&closed=false"
    
    try:
        response = requests.get(url)
        events = response.json()
        active_assets = {}

        for event in events:
            for market in event.get('markets', []):
                ticker = market.get('ticker')
                clob_ids_raw = market.get('clobTokenIds')
                
                if clob_ids_raw and ticker:
                    try:
                        token_ids = json.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
                        # Filter strictly for binary pairs
                        if len(token_ids) == 2:
                            active_assets[ticker] = {
                                "yes": token_ids[0],
                                "no": token_ids[1]
                            }
                    except:
                        continue

        with open("assets.json", "w") as f:
            json.dump(active_assets, f, indent=4)
        print(f"✅ Found {len(active_assets)} binary markets. IDs saved to assets.json")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fetch_all_binary_assets()
