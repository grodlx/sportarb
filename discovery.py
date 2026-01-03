import requests
import json

def fetch_sports_assets():
    print("🔍 Deep Scanning Polymarket for Sports Events...")
    
    # We use the /events endpoint as it is the 'source of truth' for the UI
    url = "https://gamma-api.polymarket.com/events?limit=200&active=true&closed=false"
    
    try:
        response = requests.get(url)
        events = response.json()
        active_assets = {}
        
        # Keywords to identify sports if the tag is missing
        sports_keywords = ['sports', 'nba', 'nfl', 'soccer', 'epl', 'mlb', 'nhl', 'ufc', 'tennis', 'f1']

        for event in events:
            # 1. Check if it's explicitly tagged as Sports (Tag ID 100381)
            # 2. Or if keywords exist in title, slug, or category
            title = event.get('title', '').lower()
            slug = event.get('slug', '').lower()
            category = str(event.get('category', '')).lower()
            tags = [t.get('name', '').lower() for t in event.get('tags', [])]
            
            is_sport = any(k in title or k in slug or k in category or k in tags for k in sports_keywords)

            if is_sport:
                for market in event.get('markets', []):
                    ticker = market.get('ticker')
                    # We need clobTokenIds to connect to the High-Frequency WebSocket
                    token_ids_raw = market.get('clobTokenIds')
                    
                    if token_ids_raw and ticker:
                        try:
                            token_ids = json.loads(token_ids_raw) if isinstance(token_ids_raw, str) else token_ids_raw
                            if len(token_ids) >= 2:
                                active_assets[ticker] = {
                                    "yes": token_ids[0],
                                    "no": token_ids[1]
                                }
                                print(f"  ✅ Added: {ticker}")
                        except Exception:
                            continue

        if not active_assets:
            print("❌ Still no sports found. Check your internet or if API limits are being hit.")
        else:
            with open("assets.json", "w") as f:
                json.dump(active_assets, f, indent=4)
            print(f"\n🚀 Success! Saved {len(active_assets)} markets to assets.json")
            
    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    fetch_sports_assets()
