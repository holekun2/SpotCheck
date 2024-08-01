import os
from sqlalchemy import create_engine
from flight_models import Base  # Make sure this import is correct

DATABASE_URL = "sqlite:///flight_inspection.db"  # Adjust if your database URL is different

def reset_database():
    # Delete the existing database file
    if os.path.exists("flight_inspection.db"):
        os.remove("flight_inspection.db")
        print("Existing database deleted.")

    # Create a new engine
    engine = create_engine(DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(engine)
    print("New database created with all tables.")

if __name__ == "__main__":
    reset_database()