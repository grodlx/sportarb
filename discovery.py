import requests
import json

def fetch_sports_assets():
    print("🔍 Scanning Gamma API for Sports Asset IDs...")
    
    # Tag 100381 is the general Sports tag. 
    # We fetch events (the matches) which contain the markets (the bets).
    url = "https://gamma-api.polymarket.com/events?tag_id=100381&active=true&closed=false&limit=100"
    
    try:
        response = requests.get(url)
        events = response.json()
        
        active_assets = {}
        
        for event in events:
            # Each event can have multiple markets (Winner, Score, etc.)
            for market in event.get('markets', []):
                ticker = market.get('ticker')
                clob_ids_raw = market.get('clobTokenIds')
                
                # Verify we have exactly two outcomes (YES/NO) and valid IDs
                if clob_ids_raw and ticker:
                    try:
                        # Sometimes clobTokenIds is a JSON string, sometimes a list
                        clob_ids = json.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
                        
                        if len(clob_ids) == 2:
                            active_assets[ticker] = {
                                "yes": clob_ids[0],
                                "no": clob_ids[1]
                            }
                    except:
                        continue
        
        with open("assets.json", "w") as f:
            json.dump(active_assets, f, indent=4)
            
        print(f"✅ Saved {len(active_assets)} sports markets to assets.json")
        
    except Exception as e:
        print(f"❌ Error during discovery: {e}")

if __name__ == "__main__":
    fetch_sports_assets()
