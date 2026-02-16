
import os
from dotenv import load_dotenv
from supabase import create_client

def verify_discs():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Missing credentials.")
        return

    try:
        supabase = create_client(url, key)
        print("Querying 'discs' table...")
        response = supabase.table("discs").select("*").execute()
        
        if response.data:
            print(f"✅ Found {len(response.data)} discs.")
            print(f"Sample: {response.data[0]['name']} ({response.data[0]['disc_type']})")
        else:
            print("⚠️ Table 'discs' is empty.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_discs()
