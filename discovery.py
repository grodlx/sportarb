import requests
import json

def fetch_sports_assets():
    print("🔍 Scanning Polymarket for any Sports-related markets...")
    
    # We use /markets directly to find active tradable items
    # Filtering for active and non-closed markets
    url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100"
    
    try:
        response = requests.get(url)
        markets = response.json()
        
        active_assets = {}
        
        for m in markets:
            # Check if 'Sports' is in the tags or group_tag
            tags = str(m.get('tags', [])).lower()
            group = str(m.get('group_tag', '')).lower()
            ticker = m.get('ticker', '')
            
            is_sport = "sport" in tags or "sport" in group or any(x in ticker for x in ["NBA", "NFL", "NHL", "EPL", "UFC"])
            
            if is_sport:
                clob_ids_raw = m.get('clobTokenIds')
                if clob_ids_raw:
                    # Parse the IDs (handles string or list format)
                    clob_ids = json.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
                    
                    if len(clob_ids) >= 2:
                        active_assets[ticker] = {
                            "yes": clob_ids[0],
                            "no": clob_ids[1]
                        }
                        print(f"  Found: {ticker}")

        if not active_assets:
            print("⚠️ No sports markets found. Polymarket might have no active sports bets right now.")
        else:
            with open("assets.json", "w") as f:
                json.dump(active_assets, f, indent=4)
            print(f"✅ Saved {len(active_assets)} markets to assets.json")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fetch_sports_assets()
