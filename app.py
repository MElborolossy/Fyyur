# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import datetime

from babel import Locale
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.functions import concat
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# connect to a local postgresql database
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#
# The relation ship will be Many-to-Many
# Show Model As Assoiciation Table
class Show(db.Model):
    __tablename__ = 'Show'

    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
    start_time = db.Column(db.String(120), primary_key=True)
    # relationships part
    artist = db.relationship("Artist")
    venue = db.relationship("Venue", cascade="delete")


# Venue Model connected with Artist through Show
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500), default="/static/img/venue.png")
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(500), default="We are on the lookout for a local artist")
    # relationShip Part
    artists = db.relationship("Show", cascade="delete")


# Artist Model connected with Venue through Show
class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500), default="/static/img/artist.png")
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(500), default="Looking for shows to perform")
    # relationShip Part
    venues = db.relationship("Show")

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

# format_datetime function is used with jijna
def format_datetime(value, format='full'):
    babel.dates.LC_TIME = Locale.parse('en_US')
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# Convert string with specific format to datetime
# used to compare the Show date to know if it is an upcoming or past show
def str_to_datetime(date):
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

# Venues home page: In this page all venues are listed
@app.route('/venues')
def venues():
    data = []
    upcoming_shows = 0
    # Get unique cities first to fill the data array in the correct way
    city_records = Venue.query.distinct(concat(Venue.city, Venue.state)).all()
    for c_record in city_records:
        venues_data = []
        # Get all the venues in each city
        venue_records = Venue.query.filter(Venue.city.like(c_record.city)) \
            .filter(Venue.state.like(c_record.state)).all()
        for v_record in venue_records:
            # Get upcoming show
            shows = v_record.artists
            for show in shows:
                if str_to_datetime(show.start_time) > datetime.utcnow():
                    upcoming_shows += 1
            # Append each venue data to the venues list
            venues_data.append({'id': v_record.id, 'name': v_record.name, 'num_upcomig_shows': upcoming_shows})
        # Append each city to the data list
        data.append({'city': c_record.city, 'state': c_record.state, 'venues': venues_data})
    return render_template('pages/venues.html', areas=data)


# Venues search : This page created to show the results of the search in the navigtion bar
@app.route('/venues/search', methods=['POST'])
def search_venues():
    # Get the result word and retrieve all the matched results from database
    # Search is case insensitive
    search_word = request.form['search_term']
    results = Venue.query.filter(Venue.name.ilike(f'%{search_word}%')).all()
    data = []
    for result in results:
        upcoming_shows = 0
        # Get upcoming show counts
        shows = result.artists
        for show in shows:
            if str_to_datetime(show.start_time) > datetime.utcnow():
                upcoming_shows += 1
        # Add the result needed data to the data object
        data.append({'id': result.id, 'name': result.name, 'num_upcoming_shows': upcoming_shows})
    # Create the response with the right way to be rendered
    response = {
        "count": len(results),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


# Venue page: This page will show each venue details data and it's show
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Use Artist form to show the name input field to search for an artist
    form = ArtistForm()
    data = {}
    # Get the required venue to show its details with its id
    required_venue = Venue.query.get(venue_id)
    # Convert genres to list to be rendered in the correct way
    required_venue.genres = (required_venue.genres.replace('{', '')).replace('}', '').split(',')
    # Update the data dictionary with the venue details 
    data.update({
        'id': required_venue.id,
        'name': required_venue.name,
        "genres": required_venue.genres,
        "address": required_venue.address,
        "city": required_venue.city,
        "state": required_venue.state,
        "phone": required_venue.phone,
        "website": required_venue.website,
        "facebook_link": required_venue.facebook_link,
        "seeking_talent": required_venue.seeking_talent,
        "seeking_description": required_venue.seeking_description,
        "image_link": required_venue.image_link
    })
    # Get the shows details for this venue by using the relationships between the tables "Models"
    past_shows = []
    upcoming_shows = []
    past_count = 0
    upcoming_count = 0
    for show in required_venue.artists:
        # Check if the show was played or will be played in upcoming days
        if str_to_datetime(show.start_time) > datetime.utcnow():
            upcoming_count += 1
            upcoming_shows.append({
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time
            })
        else:
            past_count += 1
            past_shows.append({
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time
            })
    # Update the data dictionary with the shows information
    data.update({"past_shows": past_shows})
    data.update({"upcoming_shows": upcoming_shows})
    data.update({"past_shows_count": past_count})
    data.update({"upcoming_shows_count": upcoming_count})
    return render_template('pages/show_venue.html', venue=data, form=form) 


#  Create Venue: The next two methods
#   1- GET method implement venue page
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


#   2- POST method submit the form entry
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        # Get the data from the form to save it in the database
        venue = Venue(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            address=request.form['address'],
            phone=request.form['phone'],
            genres=request.form.getlist('genres'),
            facebook_link=request.form['facebook_link']
        )
        # Add the Venue Object to the db session
        db.session.add(venue)
        db.session.commit()
    except:
        # Error handling by flash a warning message
        error = True
        db.session.rollback()
        flash(f"An error occurred. Venue {request.form['name']} could not be listed.", 'warning')
    finally:
        # Close the session to be used with other processs
        db.session.close()

    # Flash success message after correct database insertion
    if not error:
        flash(f"Venue {request.form['name']} was successfully listed!", 'info')
    # Return to the home page
    return render_template('pages/home.html')


#  Delete Venue
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        # Delete venue by id
        delete_venue = Venue.query.get(venue_id)
        db.session.delete(delete_venue)
        db.session.commit()
    except:
        # Error handling 
        error = True
        db.session.rollback()
    finally:
        # Close the session to be used with other processs
        db.session.close()

    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
# Artists: In this page all the artists will be listed
@app.route('/artists')
def artists():
    data = []
    # Get all the artist from db
    all_artists = Artist.query.all()
    for artist in all_artists:
        data.append({'id': artist.id, 'name': artist.name})
    return render_template('pages/artists.html', artists=data)

# Search artists: Search on artists with partial string search. It is case-insensitive.
@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_word = request.form['search_term']
    # Get all the results that match the search word from db
    results = Artist.query.filter(Artist.name.ilike(f'%{search_word}%')).all()
    data = []
    for result in results:
        # Update data list with the matched artists
        data.append({'id': result.id, 'name': result.name, 'num_upcoming_shows': 0})
    response = {
        "count": len(results),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))

# Artist Page: In this page all the information of the selected Artist is shown
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    data = {}
    # Get the required artist to show its details with its id
    required_artist = Artist.query.get(artist_id)
    # Convert genres to list to be rendered in the correct way
    required_artist.genres = (required_artist.genres.replace('{', '')).replace('}', '').split(',')
    # Update the data dictionary with the artist details 
    data.update({
        'id': required_artist.id,
        'name': required_artist.name,
        "genres": required_artist.genres,
        "city": required_artist.city,
        "state": required_artist.state,
        "phone": required_artist.phone,
        "website": required_artist.website,
        "facebook_link": required_artist.facebook_link,
        "seeking_venue": required_artist.seeking_venue,
        "seeking_description": required_artist.seeking_description,
        "image_link": required_artist.image_link
    })
    # Get the shows details for this artist by using the relationships between the tables "Models"
    past_shows = []
    upcoming_shows = []
    past_count = 0
    upcoming_count = 0
    for show in required_artist.venues:
        # Check if the show was played or will be played in upcoming days
        if (str_to_datetime(show.start_time) > datetime.utcnow()):
            upcoming_count += 1
            upcoming_shows.append({
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": show.start_time
            })
        else:
            past_count += 1
            past_shows.append({
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": show.start_time
            })
    # Update the data dictionary with the shows information
    data.update({"past_shows": past_shows})
    data.update({"upcoming_shows": upcoming_shows})
    data.update({"past_shows_count": past_count})
    data.update({"upcoming_shows_count": upcoming_count})

    return render_template('pages/show_artist.html', artist=data)


#  Create Artist
#  ----------------------------------------------------------------
#   1- GET method implement artist page
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

#   2- POST method submit the form entry
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        # Get the data from the form to save it in the database
        artist = Artist(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            phone=request.form['phone'],
            genres=request.form.getlist('genres'),
            facebook_link=request.form['facebook_link']
        )
        # Add the Artist Object to the db session
        db.session.add(artist)
        db.session.commit()
    except:
        # Error handling by flash a warning message
        error = True
        db.session.rollback()
        flash(f"An error occurred. Artist {request.form['name']} could not be listed.", 'info')
    finally:
        # Close the session to be used with other processs
        db.session.close()

    # Flash success message after correct database insertion
    if not error:
        flash(f"Artist {request.form['name']} was successfully listed!", 'info')
    # Return to the home page
    return render_template('pages/home.html')


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    # Get the required artist to show its details with its id
    required_artist = Artist.query.get(artist_id)
    # Convert genres to list to be rendered in the correct way
    required_artist.genres = (required_artist.genres.replace('{', '')).replace('}', '').split(',')
    artist = {
        "id": required_artist.id,
        "name": required_artist.name,
        "genres": required_artist.genres,
        "city": required_artist.city,
        "state": required_artist.state,
        "phone": required_artist.phone,
        "website": required_artist.website,
        "facebook_link": required_artist.facebook_link,
        "seeking_venue": required_artist.seeking_venue,
        "seeking_description":required_artist.seeking_description,
        "image_link": required_artist.image_link
    }
    return render_template('forms/edit_artist.html', form=form, artist=artist)

# Edit Artist
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    update_artist = Artist.query.get(artist_id)
    try:
        # Update artist information from the from entry
        update_artist.name = request.form['name']
        update_artist.genres = request.form.getlist('genres')
        update_artist.city = request.form['city']
        update_artist.state = request.form['state']
        update_artist.phone = request.form['phone']
        update_artist.facebook_link = request.form['facebook_link']
        db.session.commit()
    except:
        # Error handling by flash a warning message
        error = True
        db.session.rollback()
        flash(f"An error occurred. Artist {request.form['name']} could not be updated.", 'info')
    finally:
        # Close the session to be used with other processs
        db.session.close()

    # Flash success message after correct database insertion
    if not error:
        flash(f"Artist {request.form['name']} was successfully updated!", 'info')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    # Get the required artist to show its details with its id
    required_venue = Venue.query.get(venue_id)
    # Convert genres to list to be rendered in the correct way
    required_venue.genres = (required_venue.genres.replace('{', '')).replace('}', '').split(',')
    venue = {
        "id": required_venue.id,
        "name": required_venue.name,
        "genres": required_venue.genres,
        "address": required_venue.address,
        "city": required_venue.city,
        "state": required_venue.state,
        "phone": required_venue.phone,
        "website": required_venue.website,
        "facebook_link": required_venue.facebook_link,
        "seeking_talent": required_venue.seeking_talent,
        "seeking_description":required_venue.seeking_description,
        "image_link": required_venue.image_link
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    update_venue = Venue.query.get(venue_id)
    try:
        # Update venue information from the from entry
        update_venue.name = request.form['name']
        update_venue.genres = request.form.getlist('genres')
        update_venue.city = request.form['city']
        update_venue.state = request.form['state']
        update_venue.address = request.form['address']
        update_venue.phone = request.form['phone']
        update_venue.facebook_link = request.form['facebook_link']
        db.session.commit()
    except:
        # Error handling by flash a warning message
        error = True
        db.session.rollback()
        flash(f"An error occurred. Venue {request.form['name']} could not be updated.", 'info')
    finally:
        # Close the session to be used with other processs
        db.session.close()

    # Flash success message after correct database insertion
    if not error:
        flash(f"Venue {request.form['name']} was successfully updated!", 'info')
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Shows
#  ----------------------------------------------------------------
# Shows Page: In this page all shows will be listed
@app.route('/shows')
def shows():
    data = []
    # Get all the artist from db
    all_shows = Show.query.all()
    for show in all_shows:
        # Get Venue Object from show object data
        venue = Venue.query.get(show.venue_id)
        # Get Artist Object from show object data
        artist = Artist.query.get(show.artist_id)
        # Update data list with the show information
        data.append({"venue_id": venue.id,
                     "venue_name": venue.name,
                     "artist_id": artist.id,
                     "artist_name": artist.name,
                     "artist_image_link": artist.image_link,
                     "start_time": show.start_time
                     })
    return render_template('pages/shows.html', shows=data)

# Create Show: create a show
@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

# Create Show: create a show from venue page.
@app.route('/shows/<int:venue_id>/create/', methods=['POST'])
def create_shows_from_venue(venue_id):
    form = ShowForm()
    data = {}
    # Update the data dictionary with the show information from venue page
    data.update({'venue_id':venue_id})
    search_word = request.form['name']
    artist = Artist.query.filter(Artist.name.ilike(f'%{search_word}%')).first()
    data.update({'artist_id':artist.id})
    # Flash a message to inform the user to enter only the start_time
    flash('Please Set the Start_time only as the Venue ID and Artist ID are already filled', 'info')
    return render_template('forms/book_artist/create.html', form= form, data=data)

# POST method submit the form entry
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
         # Get the data from the form to save it in the database
        venue_object = Venue.query.get(request.form['venue_id'])
        artist_object = Artist.query.get(request.form['artist_id'])
        show = Show(
            venue=venue_object,
            artist=artist_object,
            start_time=request.form['start_time']
        )
        # Add the Show Object to the db session
        db.session.add(show)
        db.session.commit()
    except:
        # Error handling by flash a warning message
        error = True
        db.session.rollback()
        flash(f"An error occurred. Show on {request.form['start_time']} could not be listed.", 'info')
    finally:
        # Close the session to be used with other processs
        db.session.close()
    
    # Flash success message after correct database insertion
    if not error:
        flash(f"Show on {request.form['start_time']} was successfully listed!", 'info')
    # Return to the home page
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
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
