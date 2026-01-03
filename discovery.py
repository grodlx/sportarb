import requests
import json

def global_discovery():
    print("🌐 Scanning Polymarket for ALL tradeable binary assets...")
    
    # We use the /markets endpoint directly with specific tradeable filters
    # active=true & closed=false & limit=1000 to catch the whole board
    url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=1000"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        active_assets = {}
        
        for m in data:
            ticker = m.get('ticker')
            # Extract clobTokenIds - this is the "Secret Sauce" for the HHF bot
            ids_raw = m.get('clobTokenIds')
            
            if ids_raw and ticker:
                try:
                    # Some responses return IDs as a string, some as a list
                    token_ids = json.loads(ids_raw) if isinstance(ids_raw, str) else ids_raw
                    
                    # Ensure it's a binary YES/NO (exactly 2 IDs)
                    if len(token_ids) == 2:
                        active_assets[ticker] = {
                            "yes": token_ids[0],
                            "no": token_ids[1]
                        }
                except:
                    continue

        if not active_assets:
            print("❌ Still found 0. Check if the API URL is accessible from your network.")
        else:
            with open("assets.json", "w") as f:
                json.dump(active_assets, f, indent=4)
            print(f"✅ Success! Found {len(active_assets)} binary markets globally.")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    global_discovery()
