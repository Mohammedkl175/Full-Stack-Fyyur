#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for,abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from models import db,Artist,Venue,Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

# region App Configration
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)
# endregion

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

# region Filters function

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

def ValidPhoneNumber(phone):
    """ The function check string phone number validation in type xxx-xxx-xxxx
        where x is integer
    
    Args:
       phone: phone number (string)  

    Returns:
       True (is valid) or False (not valid)  
    """
    if (len(phone)) != 12:
        return False
    if(phone[3]!='-' or phone[7]!='-'):
        return False
    Phone = phone.replace('-','')
    return Phone.isnumeric()

# endregion

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    """ The function show all venues listed by a header with city and state values 

    Returns:
       Render venues page with venues names,city and state   
    """
    city_state = Venue.query.distinct(Venue.city, Venue.state).all()
    areas = []
    for venue in city_state:
        city = venue.city
        state = venue.state
        Venues = Venue.query.filter_by(city=city, state=state).all()
        venues = []
        for venue in Venues:
            id = venue.id
            name = venue.name
            num_upcoming_shows = (Show.query.filter(
                Show.venue_id == id, Show.start_time > datetime.now()).join(Venue, Show.venue)).count()
            venues.append(
                {"id": id, "name": name, "num_upcoming_shows": num_upcoming_shows})
        areas.append({"city": city, "state": state, "venues": venues})
    return render_template('pages/venues.html', areas=areas)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    """ The function search on venues with partial string search and case sensitive  

    Returns:
       Render search venues page with results of venue count and venue name   
    """
    search_venue = request.form.get('search_term')
    All_Venues = Venue.query.filter(
        Venue.name.ilike('%{}%'.format(search_venue))).all()
    result = []
    for venue in All_Venues:
        result.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": Show.query.filter(Show.venue_id == venue.id, Show.start_time > datetime.now()).count()
        })
    Response = {"count": len(All_Venues), "data": result}
    return render_template('pages/search_venues.html', results=Response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    """ The function shows the venue page with the given venue_id  
    
    Args:
       venue_id: venue id is primary key and use to query any Venue by its id 

    Returns:
       Render venues page for certain id with results of venue properties   
    """
    VenueById = Venue.query.get(venue_id)
    ShowByVenue = Show.query.filter(
        Show.venue_id == venue_id).join(Artist, Show.artist)
    past_shows_count_query = ShowByVenue.filter(
        Show.start_time < datetime.now()).count()
    past_shows_query = ShowByVenue.filter(
        Show.start_time < datetime.now()).all()
    upcoming_shows_count_query = ShowByVenue.filter(
        Show.start_time > datetime.now()).count()
    upcoming_shows_query = ShowByVenue.filter(
        Show.start_time > datetime.now()).all()

    upcoming_shows = []
    for upcoming in upcoming_shows_query:
        artist_id = upcoming.artist.id
        artist_name = upcoming.artist.name
        artist_image_link = upcoming.artist.image_link
        start_time = upcoming.start_time
        upcoming_shows.append({"artist_id": artist_id, "artist_name": artist_name,
                               "artist_image_link": artist_image_link, "start_time": start_time.strftime("%m/%d/%Y, %H:%M:%S")})

    past_shows = []
    for past in past_shows_query:
        artist_id = past.artist.id
        artist_name = past.artist.name
        artist_image_link = past.artist.image_link
        start_time = past.start_time
        past_shows.append({"artist_id": artist_id, "artist_name": artist_name,
                           "artist_image_link": artist_image_link, "start_time": start_time.strftime("%m/%d/%Y, %H:%M:%S")})

    venue = {"id": venue_id,
         "name": VenueById.name,
         "genres": (VenueById.genres).split(','),
         "address": VenueById.address,
         "city": VenueById.city,
         "state": VenueById.state,
         "phone": VenueById.phone,
         "website": VenueById.website,
         "facebook_link": VenueById.facebook_link,
         "seeking_talent": VenueById.seeking_talent,
         "seeking_description": VenueById.seeking_description,
         "image_link": VenueById.image_link,
         "past_shows": past_shows,
         "upcoming_shows": upcoming_shows,
         "past_shows_count": past_shows_count_query,
         "upcoming_shows_count": upcoming_shows_count_query,
         }
    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    """ The function create new venue with properties filled into Venue Form
        and insert new venue to database   

    Returns:
       Render Home Page with flash for successed or faild   
    """
    New_Venue_Form = VenueForm(request.form)
    try:
        New_Venue = Venue()
        New_Venue.name = New_Venue_Form.name.data
        New_Venue.genres = ','.join(New_Venue_Form.genres.data)
        New_Venue.city = New_Venue_Form.city.data
        New_Venue.state = New_Venue_Form.state.data
        New_Venue.phone = New_Venue_Form.phone.data
        New_Venue.address = New_Venue_Form.address.data
        New_Venue.facebook_link = New_Venue_Form.facebook_link.data
        if(not ValidPhoneNumber(New_Venue_Form.phone.data)):
            raise ValueError
        db.session.add(New_Venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except ValueError:
        db.session.rollback()
        flash('Incorrect phone number format xxx-xxx-xxxx   (' + request.form['phone']+ '),  please try again.')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + request.form['name']+ ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    """ The function query venue with its id and delete it from database  
    
    Args:
    venue_id: venue id is primary key and use to query any Venue by its id 

    Returns:
       None for successed and ERROR 400 for faild   
    """
    error=False
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        error=True
        db.session.rollback()
    finally:
        db.session.close()
    if(error):
        abort(400)
    else:
        return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    """ The function show all artists in database.

    Returns:
       Render artists page with artist name   
    """
    All_Artists = Artist.query.all()
    artists = []
    for artist in All_Artists:
        id = artist.id
        name = artist.name
        artists.append({"id": id, "name": name})
    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    """ The function search on artists with partial string search and case sensitive  

    Returns:
       Render search artists page with results of artists count and artists name   
    """
    search_artist = request.form.get('search_term')
    All_Artists_Result = Artist.query.filter(
        Artist.name.ilike('%{}%'.format(search_artist))).all()
    artists = []
    for artist in All_Artists_Result:
        artists.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": Show.query.filter(Show.artist_id == artist.id, Show.start_time > datetime.now()).count()
        })
    Response = {"count": len(All_Artists_Result), "data": artists}
    return render_template('pages/search_artists.html', results=Response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    """ The function shows the artist page with the given artist_id  
    
    Args:
    artist_id: artist id is primary key and use to query any Artist by its id 

    Returns:
       Render artists page for certain id with results of artist properties   
    """
    ArtistById = Artist.query.get(artist_id)
    ShowByArtist = Show.query.filter(
        Show.artist_id == artist_id).join(Venue, Show.venue)
    past_shows_count_query = ShowByArtist.filter(
        Show.start_time < datetime.now()).count()
    past_shows_query = ShowByArtist.filter(
        Show.start_time < datetime.now()).all()
    upcoming_shows_count_query = ShowByArtist.filter(
        Show.start_time > datetime.now()).count()
    upcoming_shows_query = ShowByArtist.filter(
        Show.start_time > datetime.now()).all()

    upcoming_shows = []
    for upcoming in upcoming_shows_query:
        venue_id = upcoming.venue.id
        venue_name = upcoming.venue.name
        venue_image_link = upcoming.venue.image_link
        start_time = upcoming.start_time
        upcoming_shows.append({"venue_id": venue_id, "venue_name": venue_name,
                               "venue_image_link": venue_image_link, "start_time": start_time.strftime("%m/%d/%Y, %H:%M:%S")})

    past_shows = []
    for past in past_shows_query:
        venue_id = past.venue.id
        venue_name = past.venue.name
        venue_image_link = past.venue.image_link
        start_time = past.start_time
        past_shows.append({"venue_id": venue_id, "venue_name": venue_name,
                           "venue_image_link": venue_image_link, "start_time": start_time.strftime("%m/%d/%Y, %H:%M:%S")})

    artist = {"id": artist_id,
         "name": ArtistById.name,
         "genres": (ArtistById.genres).split(','),
         "city": ArtistById.city,
         "state": ArtistById.state,
         "phone": ArtistById.phone,
         "website": ArtistById.website,
         "facebook_link": ArtistById.facebook_link,
         "seeking_venue": ArtistById.seeking_venue,
         "seeking_description": ArtistById.seeking_description,
         "image_link": ArtistById.image_link,
         "past_shows": past_shows,
         "upcoming_shows": upcoming_shows,
         "past_shows_count": past_shows_count_query,
         "upcoming_shows_count": upcoming_shows_count_query,
         }
    return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    """ The function request artist properties by its id from database
        and populate properties to Artist Form.   

    Args: 
       artist_id: artist id is primary key and use to query any Artist by its id 

    Returns:
       Render Edit page for artist.     
    """
    Update_Artist= Artist.query.get(artist_id)
    artist = {
        "id": Update_Artist.id,
        "name": Update_Artist.name,
        "genres": (Update_Artist.genres).split(','),
        "city": Update_Artist.city,
        "state": Update_Artist.state,
        "phone": Update_Artist.phone,
        "website": Update_Artist.website,
        "facebook_link": Update_Artist.facebook_link,
        "seeking_venue": Update_Artist.seeking_venue,
        "seeking_description": Update_Artist.seeking_description,
        "image_link": Update_Artist.image_link
    }
    form = ArtistForm(data=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    """ The function update artist properties by its id to database   

    Args: 
       artist_id: artist id is primary key and use to query any Artist by its id 

    Returns:
       Render artist page for updated artist.     
    """
    try:
        Artist_form = ArtistForm(request.form)
        Update_Artist= Artist.query.get(artist_id)
        Update_Artist.name= Artist_form.name.data
        Update_Artist.genres= (',').join(Artist_form.genres.data)
        Update_Artist.city= Artist_form.city.data
        Update_Artist.state= Artist_form.state.data
        Update_Artist.phone= Artist_form.phone.data
        Update_Artist.facebook_link= Artist_form.facebook_link.data
        if(not ValidPhoneNumber(Artist_form.phone.data)):
            raise ValueError
        db.session.commit()
    except ValueError:
        db.session.rollback()
        flash('Incorrect phone number format xxx-xxx-xxxx   (' + request.form['phone']+ '),  please try again.')
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    """ The function request venue properties by its id from database
        and populate properties to Venue Form.   

    Args: 
       venue_id: venue id is primary key and use to query any Venue by its id 

    Returns:
       Render Edit page for venue.     
    """
    Update_Venue= Venue.query.get(venue_id)
    venue = {
        "id": Update_Venue.id,
        "name": Update_Venue.name,
        "genres": (Update_Venue.genres).split(','),
        "address":Update_Venue.address,
        "city": Update_Venue.city,
        "state": Update_Venue.state,
        "phone": Update_Venue.phone,
        "website": Update_Venue.website,
        "facebook_link": Update_Venue.facebook_link,
        "seeking_telent": Update_Venue.seeking_talent,
        "seeking_description": Update_Venue.seeking_description,
        "image_link": Update_Venue.image_link
    }
    form = VenueForm(data=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    """ The function update venue properties by its id to database   

    Args: 
       venue_id: venue id is primary key and use to query any Venue by its id 

    Returns:
       Render venue page for updated venue.     
    """
    try:
        Venue_form = VenueForm(request.form)
        Update_Venue= Venue.query.get(venue_id)
        Update_Venue.name= Venue_form.name.data
        Update_Venue.genres= (',').join(Venue_form.genres.data)
        Update_Venue.address= Venue_form.address.data
        Update_Venue.city= Venue_form.city.data
        Update_Venue.state= Venue_form.state.data
        Update_Venue.phone= Venue_form.phone.data
        Update_Venue.facebook_link= Venue_form.facebook_link.data
        if(not ValidPhoneNumber(Venue_form.phone.data)):
            raise ValueError
        db.session.commit()
    except ValueError:
        db.session.rollback()
        flash('Incorrect phone number format xxx-xxx-xxxx   (' + request.form['phone']+ '),  please try again.')
    except:
        db.session.rollback()
    finally:
        db.session.close()
        
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    """ The function create new artist with properties filled into Artist Form
        and insert new artist to database   

    Returns:
       Render Home Page with flash for successed or faild   
    """
    New_Artist_Form = ArtistForm(request.form)
    try:
        New_Artist = Artist()
        New_Artist.name = New_Artist_Form.name.data
        New_Artist.genres = ','.join(New_Artist_Form.genres.data)
        New_Artist.city = New_Artist_Form.city.data
        New_Artist.state = New_Artist_Form.state.data
        New_Artist.phone = New_Artist_Form.phone.data
        New_Artist.facebook_link = New_Artist_Form.facebook_link.data
        if(not ValidPhoneNumber(New_Artist_Form.phone.data)):
            raise ValueError
        db.session.add(New_Artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except ValueError:
        db.session.rollback()
        flash('Incorrect phone number format xxx-xxx-xxxx   (' + request.form['phone']+ '),  please try again.')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    """ The function displays list of shows in database.

    Returns:
       Render shows page with artist name,venue name and start time   
    """
    # 
    All_Shows = Show.query.all()
    shows = []
    for show in All_Shows:
        show_data = {"venue_id": show.venue_id,
             "venue_name": show.venue.name,
             "artist_id": show.artist_id,
             "artist_name": show.artist.name,
             "artist_image_link": show.artist.image_link,
             "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")}
        shows.append(show_data)
    return render_template('pages/shows.html', shows=shows)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    """ The function create new show with venue id,artist id and start time
        filled into Show Form and insert new show to database   

    Returns:
       Render Home Page with flash for successed or faild   
    """
    Show_form = ShowForm(request.form)
    Valid_Artist_Id = Artist.query.get(Show_form.artist_id.data)
    Valid_Venue_Id = Venue.query.get(Show_form.venue_id.data)
    if(Valid_Venue_Id==None or Valid_Artist_Id==None):
        flash('Venue or Artist not found. Show could not be listed.')
        return render_template('pages/home.html')
    try:
        New_Show = Show()
        New_Show.venue_id = Show_form.venue_id.data
        New_Show.artist_id = Show_form.artist_id.data
        New_Show.start_time = Show_form.start_time.data
        db.session.add(New_Show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
