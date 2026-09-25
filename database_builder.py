import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

def build_database():
    print("--- Phase 1: Database Migration ---")
    
    csv_path = 'data/bi_export.csv'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Please run data_pipeline_for_bi.py first.")
        return
        
    print(f"1. Reading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found in environment.")
        return

    print("2. Connecting to PostgreSQL database...")
    engine = create_engine(db_url, pool_size=10, max_overflow=20)
    
    print("3. Creating table 'customers' and inserting data...")
    # This will replace the table if it already exists
    df.to_sql('customers', engine, if_exists='replace', index=False)
    
    print("4. Verifying insertion...")
    with engine.connect() as conn:
        # Create an index to speed up queries based on Churn Risk
        conn.execute(pd.io.sql.text('CREATE INDEX IF NOT EXISTS idx_churn_risk ON customers ("Churn Risk (%)")'))
        conn.commit()
        
        result = conn.execute(pd.io.sql.text('SELECT COUNT(*) FROM customers'))
        count = result.scalar()
        print(f"   Successfully inserted {count} records into 'customers' table.")
    
    print("\n✅ Database migration complete! You are ready to query PostgreSQL.")

if __name__ == "__main__":
    build_database()
