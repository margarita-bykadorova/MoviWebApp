from flask import Flask, render_template, request, redirect, url_for, abort
from data_manager import DataManager
from models import db, Movie
import os
import requests
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

OMDB_API_KEY = os.environ.get("OMDB_API_KEY")
app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data', 'movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Link the database and the app
db.init_app(app)

# Create an object of your DataManager class
data_manager = DataManager()


def parse_year(year_str):
    """
    Try to convert a string to a valid movie year (int).
    Returns an int or None if it's empty or invalid.
    """
    if not year_str:
        return None

    year_str = str(year_str).strip()
    if not year_str:
        return None

    try:
        year_val = int(year_str)
    except ValueError:
        return None

    return year_val

@app.route('/')
def index():
    """Show a list of all registered users and a form for adding new users."""
    users = data_manager.get_users()
    return render_template('index.html', users=users)


@app.route('/users', methods=['POST'])
def create_user():
    """Add the new user info to the database, then redirect back to the home page."""
    name = request.form.get('name')
    if not name:
        # no name entered, just go back
        return redirect(url_for('index'))
    data_manager.create_user(name)
    return redirect(url_for('index'))

@app.route('/users/<int:user_id>/movies', methods=['GET'])
def get_movies(user_id):
    """Display the user’s list of favorite movies."""
    user = data_manager.get_user(user_id)
    if user is None:
        abort(404)

    movies = data_manager.get_movies(user_id)
    return render_template('movies.html', user=user, movies=movies)

@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """
    Add a new movie to a user’s list of favorite movies.

    - Read the movie title from the form
    - Fetch details from OMDb (if possible)
    - Create a Movie instance
    - Save it via DataManager
    """
    title = request.form.get("title")
    if not title:
        # No title provided, just go back to the movies page
        return redirect(url_for("get_movies", user_id=user_id))

    # If OMDB_API_KEY is not set, fall back to basic movie with just title
    if not OMDB_API_KEY:
        movie = Movie(name=title, user_id=user_id)
        data_manager.add_movie(movie)
        return redirect(url_for("get_movies", user_id=user_id))

    try:
        response = requests.get(
            "http://www.omdbapi.com/",
            params={"t": title, "apikey": OMDB_API_KEY},
            timeout=5,
        )
        data = response.json()

        # If OMDb didn’t find the movie, store only the title
        if data.get("Response") == "False":
            movie = Movie(name=title, user_id=user_id)
        else:
            name = data.get("Title") or title
            director = data.get("Director") or None
            year_str = data.get("Year")
            poster = data.get("Poster")

            year_val = parse_year(year_str)

            if poster == "N/A":
                poster = None

            movie = Movie(
                name=name,
                director=director,
                year=year_val,
                poster_url=poster if poster != "N/A" else None,
                user_id=user_id,
            )

        data_manager.add_movie(movie)

    except Exception as exc:  # basic error handling; could be improved
        print("Error fetching OMDb data:", exc)
        # Fall back to creating a movie with only the title
        movie = Movie(name=title, user_id=user_id)
        data_manager.add_movie(movie)

    return redirect(url_for("get_movies", user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    """
    Modify the details of a specific movie in a user’s list:
    title, year, and director.
    """
    new_title = request.form.get("new_title") or None
    new_year_raw = request.form.get("new_year")
    new_director = request.form.get("new_director") or None

    year_val = parse_year(new_year_raw)

    # If nothing was provided at all, just redirect back
    if not any([new_title, new_year_raw.strip(), new_director]):
        return redirect(url_for("get_movies", user_id=user_id))

    updated = data_manager.update_movie(
        movie_id,
        title=new_title,
        year=year_val,
        director=new_director,
    )

    if updated is None:
        abort(404)

    return redirect(url_for("get_movies", user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    """Remove a specific movie from a user’s favorite movie list."""
    pass


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
