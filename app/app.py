from flask import Flask
from database import DatabaseManager
from routes import setup_routes
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)



class App:
    def __init__(self):
        self.app = Flask(__name__)
        
        database_path = os.getenv('DATABASE_PATH')
        self.db_manager = DatabaseManager(database_path)
        setup_routes(self.app, self.db_manager)

    def run(self):
        self.app.run(debug=True)

if __name__ == '__main__':
    app_instance = App()
    app_instance.run()