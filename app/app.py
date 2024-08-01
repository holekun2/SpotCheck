from flask import Flask
from database import DatabaseManager
from routes import setup_routes


DATABASE_URL = "sqlite:///app/db/flight_inspection.db"


app = Flask(__name__)



class App:
    def __init__(self):
        self.app = Flask(__name__)
        
        self.db_manager = DatabaseManager(DATABASE_URL)
        setup_routes(self.app, self.db_manager)

    def run(self):
        self.app.run(debug=True)

if __name__ == '__main__':
    app_instance = App()
    app_instance.run()