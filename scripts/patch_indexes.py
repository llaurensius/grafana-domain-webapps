import sys
import os

# Append backend directory to path so we can import app modules
sys.path.append(os.path.abspath("backend"))

from app.database import engine
from sqlalchemy import text

def apply_indexes():
    queries = [
        "CREATE INDEX IF NOT EXISTS ix_incidents_domain_id ON incidents (domain_id);",
        "CREATE INDEX IF NOT EXISTS ix_incidents_start_time ON incidents (start_time);",
        "CREATE INDEX IF NOT EXISTS ix_incidents_status ON incidents (status);",
        "CREATE INDEX IF NOT EXISTS ix_incidents_qualifies_as_downtime ON incidents (qualifies_as_downtime);"
    ]
    
    with engine.connect() as conn:
        for q in queries:
            print(f"Executing: {q}")
            conn.execute(text(q))
        conn.commit()
    print("All indexes applied successfully!")

if __name__ == "__main__":
    apply_indexes()
