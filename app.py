"""
Flask application for the Movie Library web app.

This module:
- Initializes the Flask app and database connection
- Loads configuration and external API keys from the environment
- Defines all routes for managing users and their movies
- Integrates with the DataManager and the OMDb API
- Handles adding, updating, deleting, and displaying movies
- Provides error handling and flash messaging
"""

import os

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, abort, flash

from data_manager import DataManager
from models import db, Movie

load_dotenv()

BASEDIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Secret key for sessions and flash messages
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY is not set in the environment!")
app.secret_key = secret_key

# External API key
OMDB_API_KEY = os.environ.get("OMDB_API_KEY")

# Configure SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(BASEDIR, 'data', 'movies.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Link the database and the app
db.init_app(app)

# Data manager instance
data_manager = DataManager()


def parse_year(year_str):
    """
    Convert a raw year string to an integer, if possible.

    Returns:
        int | None: Parsed year, or None if the input is empty/invalid.
    """
    if not year_str:
        return None

    year_str = str(year_str).strip()
    if not year_str:
        return None

    try:
        return int(year_str)
    except ValueError:
        return None


def create_basic_movie(title, user_id, flash_message=None, category="info"):
    """
    Create and save a movie with only a title.

    Args:
        title (str): Movie title;
        user_id (int): ID of the user who owns the movie;
        flash_message (str | None): Optional message to show the user;
        category (str): Flash category (e.g. "info", "warning").

    Returns:
        Movie: The created Movie instance.
    """
    movie = Movie(name=title, user_id=user_id)
    data_manager.add_movie(movie)
    if flash_message:
        flash(flash_message, category)
    return movie


def create_movie_from_omdb(data, fallback_title, user_id):
    """
    Create and save a Movie instance from OMDb response data.

    Uses fallback_title if the OMDb "Title" field is missing.

    Args:
        data (dict): Parsed JSON response from the OMDb API;
        fallback_title (str): Title to use if OMDb does not provide one;
        user_id (int): ID of the user who owns the movie.

    Returns:
        Movie: The created Movie instance.
    """
    name = data.get("Title") or fallback_title

    director = data.get("Director")
    if director in (None, "N/A"):
        director = None

    year_val = parse_year(data.get("Year"))

    poster = data.get("Poster")
    if poster in (None, "N/A"):
        poster = None

    movie = Movie(
        name=name,
        director=director,
        year=year_val,
        poster_url=poster,
        user_id=user_id,
    )
    data_manager.add_movie(movie)
    flash(f"Movie '{name}' added successfully!", "success")
    return movie


@app.route("/")
def index():
    """Show a list of all registered users and a form for adding new users."""
    users = data_manager.get_users()
    return render_template("index.html", users=users)


@app.route("/users", methods=["POST"])
def create_user():
    """Add a new user if the name is unique, otherwise flash a warning."""
    name = request.form.get("name")

    if not name:
        flash("Please enter a name.", "warning")
        return redirect(url_for("index"))

    # Check for existing user (case-insensitive)
    existing = data_manager.get_user_by_name(name)
    if existing:
        flash(f"User '{name}' already exists.", "warning")
        return redirect(url_for("index"))

    data_manager.create_user(name)
    flash(f"User '{name}' created successfully!", "success")
    return redirect(url_for("index"))


@app.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    """Delete a user and all their movies."""
    user = data_manager.get_user(user_id)
    if user is None:
        abort(404)

    deleted = data_manager.delete_user(user_id)
    if deleted:
        flash(f"User '{user.name}' and all their movies were deleted.", "info")
    else:
        flash("User could not be deleted.", "warning")

    return redirect(url_for("index"))


@app.route("/users/<int:user_id>/movies", methods=["GET"])
def get_movies(user_id):
    """
    Display the user’s list of favorite movies.

    Optional query parameter:
        q (str): If provided, filter movies by a search term.
    """
    user = data_manager.get_user(user_id)
    if user is None:
        abort(404)

    search_term = (request.args.get("q") or "").strip()
    movies = data_manager.get_movies(
        user_id,
        search=search_term if search_term else None,
    )

    return render_template("movies.html", user=user, movies=movies, search=search_term)


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """
    Add a movie for a given user.
    - Reads the movie title from the form
    - Enforces one-title-per-user uniqueness
    - Fetches info from OMDb (if available)
    - Falls back gracefully if data is missing or OMDb fails
    """
    # Single validation step → single early return
    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Please enter a movie title.", "warning")
        return redirect(url_for("get_movies", user_id=user_id))

    # First uniqueness check (user input title, case-insensitive)
    if data_manager.movie_exists_for_user(user_id, title):
        flash(f"Movie '{title}' is already in your library.", "warning")
        return redirect(url_for("get_movies", user_id=user_id))

    # If no API key, just create a basic movie and fall through to the final redirect
    if not OMDB_API_KEY:
        create_basic_movie(
            title=title,
            user_id=user_id,
            flash_message=(
                "Movie added using your title only. "
                "(No movie database configured.)"
            ),
            category="info",
        )
    else:
        # Try fetching from OMDb, but avoid extra returns
        try:
            response = requests.get(
                "http://www.omdbapi.com/",
                params={"t": title, "apikey": OMDB_API_KEY},
                timeout=5,
            )
            data = response.json()

            if data.get("Response") == "False":
                # OMDb didn't find the movie → basic movie only
                create_basic_movie(
                    title=title,
                    user_id=user_id,
                    flash_message=(
                        "We couldn’t find this movie in the database, "
                        "but we added it using your title only."
                    ),
                    category="warning",
                )
            else:
                # OMDb found something → use OMDb title for stricter uniqueness
                omdb_title = data.get("Title") or title

                if data_manager.movie_exists_for_user(user_id, omdb_title):
                    flash(
                        f"Movie '{omdb_title}' is already in your library.",
                        "warning",
                    )
                else:
                    create_movie_from_omdb(
                        data=data,
                        fallback_title=title,
                        user_id=user_id,
                    )

        except (requests.exceptions.RequestException, ValueError):
            # Network/JSON issues → still add a basic movie
            create_basic_movie(
                title=title,
                user_id=user_id,
                flash_message=(
                    "We couldn’t reach the movie database right now, "
                    "but we added your movie using the title you provided."
                ),
                category="warning",
            )

    # Single final return for all success paths
    return redirect(url_for("get_movies", user_id=user_id))


@app.route("/users/<int:user_id>/movies/<int:movie_id>/update", methods=["POST"])
def update_movie(user_id, movie_id):
    """
    Modify the details of a specific movie in a user's list:
    title, year, and/or director.
    """
    new_title = request.form.get("new_title") or None
    new_year_raw = request.form.get("new_year")
    new_director = request.form.get("new_director") or None

    year_val = parse_year(new_year_raw)

    # If user didn't enter anything at all
    if not any([new_title, (new_year_raw and new_year_raw.strip()), new_director]):
        flash("No changes provided to update.", "warning")
        return redirect(url_for("get_movies", user_id=user_id))

    updated = data_manager.update_movie(
        movie_id,
        title=new_title,
        year=year_val,
        director=new_director,
    )

    if updated is None:
        abort(404)

    flash("Movie updated successfully.", "success")
    return redirect(url_for("get_movies", user_id=user_id))


@app.route("/users/<int:user_id>/movies/<int:movie_id>/delete", methods=["POST"])
def delete_movie(user_id, movie_id):
    """Remove a specific movie from a user's favorite movie list."""
    success = data_manager.delete_movie(movie_id)
    if not success:
        abort(404)

    flash("Movie deleted.", "info")
    return redirect(url_for("get_movies", user_id=user_id))


@app.errorhandler(404)
def page_not_found(_error):
    """Render custom 404 page."""
    return render_template("404.html"), 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    # For production (e.g. PythonAnywhere) debug should be disabled.
    app.run(debug=True)
