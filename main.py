from app.app import app_instance


app = app_instance.app

if __name__ == '__main__':
    app_instance.run()