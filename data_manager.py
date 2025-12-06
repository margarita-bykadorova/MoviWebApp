"""
Data Manager module for interacting with the database.

Provides CRUD operations for:
- Users
- Movies
using SQLAlchemy ORM.
"""

from sqlalchemy import func

from models import db, User, Movie


class DataManager:
    """Data access layer for users and movies."""

    def get_user_by_name(self, name):
        """
        Return a user by name (case-insensitive), or None if not found.

        Args:
            name (str): The user's name to search for.
        """
        return User.query.filter(func.lower(User.name) == func.lower(name)).first()

    def create_user(self, name):
        """
        Add a new user to the database and return the created User.

        Args:
            name (str): Name of the new user.
        """
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit()
        return new_user

    def get_users(self):
        """Return a list of all users in the database."""
        return User.query.all()

    def get_user(self, user_id):
        """
        Return a single user by ID, or None if not found.

        Args:
            user_id (int): The ID of the user.
        """
        return User.query.get(user_id)

    def get_movies(self, user_id, search=None):
        """
        Return a list of all movies belonging to a specific user.

        If 'search' is provided, filter movies by title (case-insensitive).

        Args:
            user_id (int): The owner user ID.
            search (str | None): Optional search term for movie title.

        Returns:
            list[Movie]: Movies belonging to the user (possibly filtered).
        """
        query = Movie.query.filter_by(user_id=user_id)

        if search:
            query = query.filter(Movie.name.ilike(f"%{search}%"))

        return query.all()

    def movie_exists_for_user(self, user_id, title):
        """
        Check if a movie with this title already exists for the given user.

        The check is case-insensitive and ignores leading/trailing spaces.

        Args:
            user_id (int): The owner user ID.
            title (str): Movie title to check.

        Returns:
            bool: True if a matching movie exists, False otherwise.
        """
        if not title:
            return False

        normalized = title.strip()
        if not normalized:
            return False

        existing = Movie.query.filter(
            Movie.user_id == user_id,
            func.lower(Movie.name) == func.lower(normalized),
        ).first()

        return existing is not None

    def add_movie(self, movie):
        """
        Add a new movie to a user's favorites.

        Expects 'movie' to be a Movie instance
        with all fields already set.

        Args:
            movie (Movie): The movie to add.

        Returns:
            Movie: The persisted Movie instance.
        """
        db.session.add(movie)
        db.session.commit()
        return movie

    def update_movie(self, movie_id, title=None, year=None, director=None):
        """
        Update the fields of a movie.

        Parameters may be:
        - title: str or None
        - year: int or None
        - director: str or None

        Empty strings are ignored.

        Returns:
            Movie | None: The updated movie, or None if not found.
        """
        movie = Movie.query.get(movie_id)
        if movie is None:
            return None

        if title:
            movie.name = title
        if year is not None:
            movie.year = year
        if director:
            movie.director = director

        db.session.commit()
        return movie

    def delete_movie(self, movie_id):
        """
        Delete a movie by ID.

        Returns:
            bool: True if deleted, False if movie not found.
        """
        movie = Movie.query.get(movie_id)
        if movie is None:
            return False

        db.session.delete(movie)
        db.session.commit()
        return True

    def delete_user(self, user_id):
        """
        Delete a user and all their movies.

        Returns:
            bool: True if the user existed and was deleted, False otherwise.
        """
        user = User.query.get(user_id)
        if user is None:
            return False

        # Movies are removed via cascade="all, delete" defined on the relationship
        db.session.delete(user)
        db.session.commit()
        return True
