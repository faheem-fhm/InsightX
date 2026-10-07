import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend"))

from app.database.session import engine, Base
from app.models import User, Dataset, DatasetSchema, DataQualityReport, AnalysisSession, RootCauseInvestigation, AIConversation

def init_database():
    print("Connecting to database and creating schema tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables verified and created successfully:")
    for table_name in Base.metadata.tables.keys():
        print(f"  [+] Table: {table_name}")

if __name__ == "__main__":
    init_database()
