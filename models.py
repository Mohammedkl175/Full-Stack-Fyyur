from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import datetime

db = SQLAlchemy()

# region Models

# region Shows table
class Show(db.Model):
    __tablename__ = 'Shows'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'Venue.id'))
    venue = db.relationship(
        'Venue', backref=db.backref('Shows', cascade='all, delete'))
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'))
    artist = db.relationship(
        'Artist', backref=db.backref('Shows', cascade='all, delete'))
    start_time = db.Column(db.DateTime())
# endregion

# region Venue table
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean())
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(120))
    artist = db.relationship('Artist', secondary="Shows",
                             backref=db.backref('Venue', lazy=True))
# endregion

# region Artist table
class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean())
    seeking_description = db.Column(db.String(500))
    website = db.Column(db.String(120))
    venue = db.relationship('Venue', secondary="Shows",
                            backref=db.backref('Artist', lazy=True))
# endregion

# endregion