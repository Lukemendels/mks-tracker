
import os
from dotenv import load_dotenv
from supabase import create_client

def verify_connection():
    print("Loading environment variables...")
    load_dotenv()
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not url:
        print("❌ Error: SUPABASE_URL not found in environment.")
        return
    if not key:
        print("❌ Error: Supabase Key (SERVICE or KEY) not found in environment.")
        return
        
    print(f"✅ Found Credentials.")
    print(f"   URL: {url[:20]}...")
    print(f"   KEY: {key[:10]}...")
    
    try:
        print("\nConnecting to Supabase...")
        supabase = create_client(url, key)
        
        print("Attempting to read 'mindset_axioms' table...")
        response = supabase.table("mindset_axioms").select("*").limit(1).execute()
        
        if response.data:
            print("✅ Connection Successful!")
            print(f"   Read {len(response.data)} record(s).")
            print(f"   First record: {response.data[0]['short_name']}")
        else:
            print("⚠️ Connection successful, but table 'mindset_axioms' is empty or not accessible.")
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    verify_connection()
