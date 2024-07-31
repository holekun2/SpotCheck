from flask import Flask
from database import DatabaseManager
from routes import setup_routes
from custom_json_encoder import CustomJSONEncoder


DATABASE_URL = "sqlite:///flight_inspection.db"


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder


class App:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.json_encoder = CustomJSONEncoder
        self.db_manager = DatabaseManager(DATABASE_URL)
        setup_routes(self.app, self.db_manager)

    def run(self):
        self.app.run(debug=True)

if __name__ == '__main__':
    app_instance = App()
    app_instance.run()