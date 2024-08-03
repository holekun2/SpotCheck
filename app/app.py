from flask import Flask
from .database import DatabaseManager
from .routes import setup_routes
from dotenv import load_dotenv
import os

load_dotenv()

class App:
    def __init__(self):
        self.app = Flask(__name__)
        
        bucket_name = os.getenv('BUCKET_NAME', 'flight-database')
        db_filename = os.getenv('DB_FILENAME', 'flight_inspection.db')
        
        self.db_manager = DatabaseManager(bucket_name, db_filename)
        self.db_manager.initialize_db()  # Initialize the database
        
        setup_routes(self.app, self.db_manager)

    def run(self):
        self.app.run(debug=True)

app_instance = App()
app = app_instance.app