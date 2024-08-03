from google.cloud import storage
from google.api_core import exceptions
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from .flight_models import Base

class DatabaseManager:
    def __init__(self, bucket_name='flight-database', db_filename='flight_inspection.db'):
        self.bucket_name = bucket_name
        self.db_filename = db_filename
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.bucket_name)
        self.local_db_path = os.path.join(tempfile.gettempdir(), self.db_filename)
        self.engine = None
        self.SessionLocal = None

    def initialize_db(self):
        try:
            self.download_db()
        except exceptions.NotFound:
            print(f"Database file not found in Cloud Storage. Creating a new one.")
            self.create_new_db()
        
        self.engine = create_engine(f'sqlite:///{self.local_db_path}', echo=False)
        self.SessionLocal = scoped_session(sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine,
            expire_on_commit=False
        ))

    def download_db(self):
        blob = self.bucket.blob(self.db_filename)
        blob.download_to_filename(self.local_db_path)

    def upload_db(self):
        blob = self.bucket.blob(self.db_filename)
        blob.upload_from_filename(self.local_db_path)

    def create_new_db(self):
        engine = create_engine(f'sqlite:///{self.local_db_path}', echo=False)
        Base.metadata.create_all(engine)
        print("New database created with all tables.")
        self.upload_db()

    @contextmanager
    def get_db(self):
        if not self.engine or not self.SessionLocal:
            self.initialize_db()
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
            self.upload_db()

    def create_tables(self):
        if not self.engine:
            self.initialize_db()
        Base.metadata.create_all(bind=self.engine)
        print("Database tables created or updated successfully.")
        self.upload_db()