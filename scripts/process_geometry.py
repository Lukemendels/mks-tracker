import os
import sys
import requests
from supabase import create_client
from geopy.distance import geodesic
from dotenv import load_dotenv

# Load env from parent dir if needed, or current
load_dotenv()

# Setup Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_elevation(lat, lon):
    """Fetch elevation in feet from USGS EPQS API."""
    try:
        url = f"https://epqs.nationalmap.gov/v1/json?x={lon}&y={lat}&wkid=4326&units=Feet&includeDate=false"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if 'value' in data:
             return float(data['value'])
        return None
    except Exception as e:
        print(f"Error fetching elevation for {lat}, {lon}: {e}")
        return None

def process_geometry():
    print("🔍 Scanning for unprocessed geometry...")
    
    # Fetch rows where distance is NULL but we have coords
    # Note: 'is' operator checks for NULL in postgrest
    res = supabase.table("hole_geometry")\
        .select("*")\
        .not_.is_("tee_lat", "null")\
        .not_.is_("basket_lat", "null")\
        .is_("distance_feet", "null")\
        .execute()
        
    rows = res.data
    if not rows:
        print("✅ No unprocessed records found.")
        return

    print(f"🔄 Processing {len(rows)} records...")
    
    for row in rows:
        try:
            hole_str = f"Hole {row['hole_number']} ({row['layout']})"
            tee = (row['tee_lat'], row['tee_lon'])
            basket = (row['basket_lat'], row['basket_lon'])
            
            # 1. Calculate Distance
            # geodesic returns km by default, .feet for feet
            dist_feet = geodesic(tee, basket).feet
            
            # 2. Fetch Elevations
            elev_tee = get_elevation(tee[0], tee[1])
            elev_basket = get_elevation(basket[0], basket[1])
            
            elev_delta = None
            if elev_tee is not None and elev_basket is not None:
                # Positive delta means uphill? 
                # Usually elevation change is Basket - Tee. 
                # If Basket (100) < Tee (120), result is -20 (Downhill).
                elev_delta = elev_basket - elev_tee
            
            print(f"   > {hole_str}: {dist_feet:.1f} ft | Δ {elev_delta} ft")
            
            # 3. Update DB
            update_payload = {
                "distance_feet": round(dist_feet, 1),
                "elevation_change_feet": round(elev_delta, 1) if elev_delta is not None else None
            }
            
            supabase.table("hole_geometry").update(update_payload).eq("id", row['id']).execute()
            
        except Exception as e:
            print(f"❌ Failed to process {row.get('id')}: {e}")

if __name__ == "__main__":
    process_geometry()
