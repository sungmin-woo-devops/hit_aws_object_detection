from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")
    return create_client(url, key)

if __name__ == "__main__":
    supabase: Client = get_supabase_client()
    print(supabase)
