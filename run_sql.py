import os
import sys
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def get_db_connection():
    """Constructs the database connection string and connects."""
    supabase_url = os.environ.get("SUPABASE_URL")
    db_password = os.environ.get("SUPABASE_DB_PASSWORD")

    if not supabase_url or not db_password:
        print("Error: Missing SUPABASE_URL or SUPABASE_DB_PASSWORD in .env")
        sys.exit(1)

    # Extract project ID from URL (https://[project-ref].supabase.co)
    parsed_url = urlparse(supabase_url)
    project_ref = parsed_url.hostname.split('.')[0]
    
    # Construct standard Supabase connection string
    # Host: db.[project-ref].supabase.co
    # User: postgres
    # Port: 5432
    # Db: postgres
    host = f"db.{project_ref}.supabase.co"
    
    try:
        conn = psycopg2.connect(
            host=host,
            database="postgres",
            user="postgres",
            password=db_password,
            port=5432
        )
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

def run_sql_file(filename):
    """Reads and executes a SQL file."""
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found.")
        sys.exit(1)

    print(f"Connecting to database...")
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        with open(filename, 'r') as f:
            sql = f.read()
        
        print(f"Executing {filename}...")
        cur.execute(sql)
        conn.commit()
        print("Success! SQL executed.")
        
    except Exception as e:
        conn.rollback()
        print(f"Execution failed: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_sql.py <file.sql>")
        # Verification mode if no args
        print("No file provided. Testing connection only...")
        conn = get_db_connection()
        print("Connection successful!")
        conn.close()
    else:
        run_sql_file(sys.argv[1])
