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
    """Show a list of all registered users and a form for adding new users."""
    return "Welcome to MoviWeb App!"


@app.route('/users', methods=['POST'])
def add_user():
    """Add the new user info to the database, then redirect back to the home page."""
    pass


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def get_user_movies(user_id):
    """Display the user’s list of favorite movies."""
    pass


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_user_movie(user_id):
    """
    Add a new movie to a user’s list of favorite movies.
      - read the movie title from the form
      - fetch details from OMDb
      - create a Movie instance
      - save it via data_manager.add_movie(movie)
    """
    pass


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    """
    Modify the title of a specific movie in a user’s list,
    without depending on OMDb for corrections.
    """
    pass


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    """Remove a specific movie from a user’s favorite movie list."""
    pass


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
