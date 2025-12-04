from flask import Flask
from data_manager import DataManager
from models import db, Movie
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data', 'movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Link the database and the app
db.init_app(app)

# Create an object of your DataManager class
data_manager = DataManager()


@app.route('/')
def home():
    return "Welcome to MoviWeb App!"


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
