#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from config import SQLALCHEMY_DATABASE_URI
from flask_migrate import Migrate
from forms import *
from datetime import datetime
from models import db, Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#





#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  venues = Venue.query.all()
  now = datetime.now()
  cities = []
  data = []
  for venue in venues:
    venue_data ={}
    venue_details={}
    if venue.city not in cities:
       venue_data['city'] = venue.city
       venue_data['state'] = venue.state
       venue_data['venues'] = []
       venue_details['id'] = venue.id
       venue_details['name'] = venue.name
       venue_details['num_upcoming_shows'] = Show.query.filter(Show.venue_id==venue.id, Show.start_time > now ).count()
       venue_data['venues'].append(venue_details)
       data.append(venue_data)
       cities.append(venue.city)
    else:
      venue_details['id'] = venue.id
      venue_details['name'] = venue.name
      venue_details['num_upcoming_shows'] = Show.query.filter(Show.venue_id==venue.id, Show.start_time > now ).count()
      index = cities.index(venue.city)
      data[index]['venues'].append(venue_details)
  
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term=request.form.get('search_term', '')
  venues= Venue.query.filter(Venue.name.ilike('%'+search_term+'%'))
  data =[]
  now = datetime.now()
  for venue in venues:
    venue_details ={}
    venue_details['id'] = venue.id 
    venue_details['name'] = venue.name
    venue_details['num_upcoming_shows'] = Show.query.filter(Show.venue_id==venue.id, Show.start_time > now ).count()
    data.append(venue_details)
  response={
    "count": venues.count(),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  shows = Show.query.join(
    Venue
  ).join(
      Artist, 
    ).filter(Artist.id == Show.artist_id).filter(venue_id== Show.venue_id).with_entities(Show.artist_id, Artist.name.label('artist_name'),Artist.image_link.label('artist_image_link'), Show.start_time)
 
  now = datetime.now()
  venue_data = {}
  venue_data = venue.__dict__
  venue_data['genres'] = venue_data['genres'].split(",")
  venue_data['upcoming_shows'] =[]
  venue_data['past_shows'] = []
  past_shows_count =0
  upcoming_shows_count = 0
  for show in shows:
    showdata ={}
    if show.start_time>now:
        showdata['artist_id'] = show.artist_id
        showdata['artist_name'] = show.artist_name
        showdata['artist_image_link'] = show.artist_image_link
        showdata['start_time'] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        venue_data['upcoming_shows'].append(showdata)
        upcoming_shows_count = upcoming_shows_count +1
    else:
        showdata['artist_id'] = show.artist_id
        showdata['artist_name'] = show.artist_name
        showdata['artist_image_link'] = show.artist_image_link
        showdata['start_time'] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        venue_data['past_shows'].append(showdata)
        past_shows_count = past_shows_count +1


    venue_data['past_shows_count'] = past_shows_count
    venue_data['upcoming_shows_count'] =upcoming_shows_count

  return render_template('pages/show_venue.html', venue=venue_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm()
  error = False
  
  try:
    venue = Venue()
    venue.name = request.form['name']
    venue.state = request.form['state'] 
    venue.city =request.form['city']
    venue.address = request.form['address']
    venue.phone = request.form['phone'].strip()
    venue.genres = (',').join(request.form.getlist('genres'))
    venue.facebook_link = request.form['facebook_link']
    venue.image_link = request.form['image_link']
    venue.website_link = request.form['website_link']
    venue.seeking_talent =True if request.form.get('seeking_talent') =='y' or request.form.get('seeking_talent')=='t' else False
    venue.seeking_description = request.form['seeking_description']
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    print(e)
    db.session.rollback()
    error = True
    flash('An error occurred. Venue ' +  request.form['name']+ ' could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return render_template('pages/home.html')


  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    venue = Venue.query.get(venue_id)
    shows = Show.query.filter_by(venue_id=venue.id).all()
    for show in shows:
        db.session.delete(show)

    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally: 
    db.session.close()
  if error:
    abort(500)
  else:
    return render_template('pages/home.html')

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  data =[]
  for artist in artists:
    data.append({'id':artist.id, 'name': artist.name})
#   data=[{
#     "id": 4,
#     "name": "Guns N Petals",
#   }, {
#     "id": 5,
#     "name": "Matt Quevedo",
#   }, {
#     "id": 6,
#     "name": "The Wild Sax Band",
#   }]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term=request.form.get('search_term', '')
  artists= Artist.query.filter(Artist.name.ilike('%'+search_term+'%'))
  data =[]
  now = datetime.now()
  for artist in artists:
    artist_details ={}
    artist_details['id'] = artist.id 
    artist_details['name'] = artist.name
    artist_details['num_upcoming_shows'] = Show.query.filter(Show.artist_id==artist.id, Show.start_time > now ).count()
    data.append(artist_details)
  response={
    "count": artists.count(),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  artist = Artist.query.get(artist_id)
  shows = Show.query.join(
    Venue
  ).join(
      Artist, 
    ).filter(Venue.id == Show.venue_id).filter(artist_id== Show.artist_id).with_entities(Show.venue_id, Venue.name.label('venue_name'),Venue.image_link.label('venue_image_link'), Show.start_time)
 
  now = datetime.now()
  artist_data = {}
  artist_data = artist.__dict__
  artist_data['genres'] = artist_data['genres'].split(",")
  artist_data['upcoming_shows'] =[]
  artist_data['past_shows']=[]
  past_shows_count =0
  upcoming_shows_count = 0
  for show in shows:
    showdata ={}
    if show.start_time>now:
        showdata['venue_id'] = show.venue_id
        showdata['venue_name'] = shows.venue_name
        showdata['venue_image_link'] = shows.venue_image_link
        showdata['start_time'] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        artist_data['upcoming_shows'].append(showdata)
        upcoming_shows_count = upcoming_shows_count +1
    else:
        showdata['venue_id'] = show.venue_id
        showdata['venue_name'] = show.venue_name
        showdata['venue_image_link'] = show.venue_image_link
        showdata['start_time'] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        artist_data['past_shows'].append(showdata)
        past_shows_count = past_shows_count +1


    artist_data['past_shows_count'] = past_shows_count
    artist_data['upcoming_shows_count'] =upcoming_shows_count

  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artistData = Artist.query.get(artist_id)
    artist= artistData.__dict__

    return render_template('forms/edit_artist.html', form=form, artist=artist)
  
  # TODO: populate form with fields from artist with ID <artist_id>
  

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
    form = ArtistForm()
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.state = request.form['state'] 
        artist.city =request.form['city']
        artist.phone =request.form['phone'].strip()
        artist.genres = (',').join(request.form.getlist('genres'))
        artist.facebook_link = request.form['facebook_link']
        artist.image_link = request.form['image_link']
        artist.website = request.form['website_link']
        artist.seeking_venue =True if request.form.get('seeking_venue') =='y' or request.form.get('seeking_talent')=='t' else False
        artist.seeking_description = request.form['seeking_description']
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venueData = Venue.query.get(venue_id)
  venue= venueData.__dict__
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
    form = VenueForm()
    error = False
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form['name']
        venue.state = request.form['state'] 
        venue.city =request.form['city']
        venue.address = request.form['address']
        venue.phone =request.form['phone'].strip()
        venue.genres = (',').join(request.form.getlist('genres'))
        venue.facebook_link = request.form['facebook_link']
        venue.image_link = request.form['image_link']
        venue.website_link = request.form['website_link']
        venue.seeking_talent =True if request.form.get('seeking_talent') =='y' or request.form.get('seeking_talent')=='t' else False
        venue.seeking_description = request.form['seeking_description']
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm()
  error = False
  try:
    artist = Artist()
    artist.name = request.form['name']
    artist.state = request.form['state'] 
    artist.city =request.form['city']
    artist.phone =request.form['phone'].strip()
    artist.genres = (',').join(request.form.getlist('genres'))
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    artist.website = request.form['website_link']
    artist.seeking_venue =True if request.form.get('seeking_venue') =='y' or request.form.get('seeking_talent')=='t' else False
    artist.seeking_description = request.form['seeking_description']
    
    db.session.add(artist)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    print(e)
    db.session.rollback()
    error = True
    flash('An error occurred. Venue ' +  request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return render_template('pages/home.html')
  
  # on successful db insert, flash success
  #flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows = Show.query.join(
    Venue
  ).join(
      Artist, 
    ).filter(Venue.id == Show.venue_id).filter(Artist.id == Show.artist_id).with_entities(Show.venue_id, Venue.name.label('venue_name'), Show.artist_id, Artist.name.label('artist_name'), Artist.image_link, Show.start_time)
  data =[]
  for show in shows:
    show_details = {}
    show_details['venue_id']  = show.venue_id
    show_details['venue_name'] =show.venue_name
    show_details['artist_id'] = show.artist_id
    show_details['artist_name'] = show.artist_name
    show_details['artist_image_link'] = show.image_link
    show_details['start_time'] =show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    data.append(show_details) 

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm()
  error = False
  try:
    show = Show()
    show.artist_id= request.form['artist_id']
    show.venue_id = request.form['venue_id']
    show.start_time =request.form.get('start_time')
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as e:
    print(e)
    db.session.rollback()
    error = True
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return render_template('pages/home.html')
  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  

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
