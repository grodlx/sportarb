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
                
                #
