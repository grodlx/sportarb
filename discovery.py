import requests
import json
from pathlib import Path

# Use the CLOB endpoint directly - this is where the trades happen
CLOB_API = "https://clob.polymarket.com/markets"

def global_discovery():
    print("🌐 Querying CLOB for all live tradeable markets...")
    all_assets = {}
    next_cursor = ""
    
    try:
        # CLOB uses a cursor-based pagination
        while True:
            url = f"{CLOB_API}?next_cursor={next_cursor}" if next_cursor else CLOB_API
            resp = requests.get(url).json()
            
            markets = resp.get('data', [])
            for m in markets:
                # We only want YES/NO binary pairs
                tokens = m.get('tokens', [])
                if len(tokens) == 2:
                    # m['question'] is the title
                    ticker = m.get('question', 'Unknown')
                    all_assets[ticker] = {
                        "yes": tokens[0]['token_id'],
                        "no": tokens[1]['token_id']
                    }
            
            next_cursor = resp.get('next_cursor', "")
            if not next_cursor or next_cursor == "none":
                break
                
        if all_assets:
            Path("assets.json").write_text(json.dumps(all_assets, indent=4))
            print(f"✅ Success! Found {len(all_assets)} live binary markets.")
        else:
            print("❌ No markets found. Verify your internet connection.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    global_discovery()
