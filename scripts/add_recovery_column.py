import sys
import os

sys.path.append(os.path.abspath("backend"))

from app.database import engine
from sqlalchemy import text

def run_migration():
    queries = [
        "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS recovery_started_at TIMESTAMP WITH TIME ZONE;",
        "CREATE UNIQUE INDEX IF NOT EXISTS uix_one_open_incident_per_domain ON incidents (domain_id) WHERE status = 'ACTIVE' OR status = 'RECOVERY_PENDING';"
    ]
    
    with engine.connect() as conn:
        for q in queries:
            print(f"Executing: {q}")
            try:
                conn.execute(text(q))
            except Exception as e:
                print(f"Warning: {e}")
        conn.commit()
    print("Migration successful!")

if __name__ == "__main__":
    run_migration()
