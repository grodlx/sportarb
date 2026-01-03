import requests
import json
from datetime import datetime, timedelta, timezone

def fetch_all_binary_assets():
    print("🔍 Scanning for ALL binary markets expiring within 7 days...")
    
    # 7-day limit in seconds
    EXPIRY_LIMIT_SECONDS = 7 * 24 * 60 * 60
    NOW = datetime.now(timezone.utc)
    
    url = "https://gamma-api.polymarket.com/events?limit=500&active=true&closed=false"
    
    try:
        response = requests.get(url)
        events = response.json()
        active_assets = {}

        for event in events:
            # Parse the end date of the event
            end_date_str = event.get('endDate')
            if not end_date_str:
                continue
                
            try:
                # Gamma API typically returns ISO format: 2026-01-10T23:59:00Z
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                time_remaining = (end_date - NOW).total_seconds()
                
                # Filter: Must expire in more than 0 seconds but less than 7 days
                if 0 < time_remaining <= EXPIRY_LIMIT_SECONDS:
                    for market in event.get('markets', []):
                        ticker = market.get('ticker')
                        token_ids_raw = market.get('clobTokenIds')
                        
                        if token_ids_raw and ticker:
                            token_ids = json.loads(token_ids_raw) if isinstance(token_ids_raw, str) else token_ids_raw
                            if len(token_ids) == 2:
                                active_assets[ticker] = {
                                    "yes": token_ids[0],
                                    "no": token_ids[1],
                                    "expires": end_date_str
                                }
                                print(f"  ✅ Included: {ticker} (Expires: {end_date_str})")
            except Exception as e:
                continue

        with open("assets.json", "w") as f:
            json.dump(active_assets, f, indent=4)
        print(f"\n🚀 Success! Found {len(active_assets)} markets meeting the 7-day criteria.")
            
    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    fetch_all_binary_assets()
