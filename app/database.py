from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from .flight_models import *
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_PATH = os.getenv('DATABASE_PATH')

class DatabaseManager:
    def __init__(self, database_url):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = scoped_session(sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine,
            expire_on_commit=False  # This disables SQLAlchemy's query cache
        ))
        self.create_tables()

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
        print("Database tables created or updated successfully.")

    @contextmanager
    def get_db(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
            
    def query_all(self):
        with self.get_db() as db:
            flights = db.query(Flight).all()
            photos = db.query(Photo).all()
            audit_entries = db.query(AuditEntry).all()
            flight_analyses = db.query(FlightAnalysis).all()
            site_inspections = db.query(SiteInspection).all()
            inspections = db.query(Inspection).all()

            print("\n=== Database Contents ===\n")

            print(f"Flights ({len(flights)}):")
            for flight in flights:
                print(f"  {repr(flight)}")
            
            print(f"\nPhotos ({len(photos)}):")
            for photo in photos:
                print(f"  {repr(photo)}")
            
            print(f"\nAudit Entries ({len(audit_entries)}):")
            for entry in audit_entries:
                print(f"  {repr(entry)}")
            
            print(f"\nFlight Analyses ({len(flight_analyses)}):")
            for analysis in flight_analyses:
                print(f"  {repr(analysis)}")
            
            print(f"\nSite Inspections ({len(site_inspections)}):")
            for inspection in site_inspections:
                print(f"  {repr(inspection)}")
            
            print(f"\nInspections ({len(inspections)}):")
            for inspection in inspections:
                print(f"  {repr(inspection)}")

            print("\n" + "=" * 30 + "\n")

            return {
                "flights": flights,
                "photos": photos,
                "audit_entries": audit_entries,
                "flight_analyses": flight_analyses,
                "site_inspections": site_inspections,
                "inspections": inspections
            }
            
        
if __name__ == "__main__":
    db_manager = DatabaseManager(DATABASE_PATH)
    all_records = db_manager.query_all()

    for table_name, records in all_records.items():
        print(f"Table: {table_name}")
        for record in records:
            print(record)