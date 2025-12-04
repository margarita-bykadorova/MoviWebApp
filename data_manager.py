from models import db, User, Movie


class DataManager:
    """Data access layer for users and movies."""

    def create_user(self, name):
        """Add a new user to the database."""
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit()
        return new_user

    def get_users(self):
        """Return a list of all users in the database."""
        return User.query.all()

    def get_user(self, user_id):
        """Return a single user by ID, or None if not found."""
        return User.query.get(user_id)

    def get_movies(self, user_id):
        """Return a list of all the movies for a specific user."""
        return Movie.query.filter_by(user_id=user_id).all()

    def add_movie(self, movie):
        """
        Add a new movie to a user's favorites.

        Expects 'movie' to be a Movie instance that already has
        its fields (name, director, year, poster_url, user_id) set.
        """
        db.session.add(movie)
        db.session.commit()
        return movie

    def update_movie(self, movie_id, title=None, year=None, director=None):
        """
        Update fields of a specific movie in the database.
        Any of title, year, director may be provided.
        """
        movie = Movie.query.get(movie_id)
        if movie is None:
            return None

        if title:
            movie.name = title
        if year is not None:
            movie.year = year
        if director is not None:
            movie.director = director

        db.session.commit()
        return movie

    def delete_movie(self, movie_id):
        """Delete a movie from the user's list of favorites."""
        movie = Movie.query.get(movie_id)
        if movie is None:
            return
        db.session.delete(movie)
        db.session.commit()
