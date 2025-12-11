"""
SQLAlchemy ORM models for the MoviWeb application.

Contains two models:
- User: represents an application user.
- Movie: represents a movie saved by a user.
"""

# pylint: disable=import-error
# pylint: disable=too-few-public-methods

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Represents a registered user in the MoviWeb app."""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    # Relationship: one user → many movies
    # Cascade ensures movies are deleted when the user is deleted.
    movies = db.relationship(
        "Movie",
        back_populates="user",
        cascade="all, delete",
        lazy=True
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} name='{self.name}'>"


class Movie(db.Model):
    """Represents a movie saved by a user."""
    __tablename__ = "movie"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    director = db.Column(db.String(100))
    year = db.Column(db.Integer)
    poster_url = db.Column(db.String(200))

    # Link Movie → User
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Explicit relationship
    user = db.relationship("User", back_populates="movies")

    def __repr__(self):
        return f"<Movie id={self.id} name={self.name!r} user_id={self.user_id}>"