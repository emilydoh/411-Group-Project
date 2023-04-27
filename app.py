from flask import Flask, render_template, request, session, redirect, url_for
from weather import main as get_weather
import string as string
import time
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

app = Flask("411-Group-Project")

# set the name of the session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# set a random secret key to sign the cookie
app.secret_key = 'YOUR_SECRET_KEY'

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'

weather= ""

# set the name of the session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# set a random secret key to sign the cookie
app.secret_key = 'YOUR_SECRET_KEY'

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'

weather=""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/home")
def login():
    # create a SpotifyOAuth instance and get the authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()
    # redirect the user to the authorization URL
    return redirect(auth_url)

# route to handle the redirect URI after authorization
@app.route('/redirect')
def redirect_page():
    # clear the session
    session.clear()
    # get the authorization code from the request parameters
    code = request.args.get('code')
    # exchange the authorization code for an access token and refresh token
    token_info = create_spotify_oauth().get_access_token(code)
    # save the token info in the session
    session[TOKEN_INFO] = token_info
    # redirect the user to the save_discover_weekly route
    return redirect(url_for('make_playlist',_external=True))


# ******************************USES PLACEHOLDER VALENCE SCORE BOUNDS, WE NEED TO PASS IT IN SOMEHOW **********************************************
# this route should generate the playlist Weatherify, and populate it with songs based on the user's top tracks
@app.route('/makePlaylist')
def make_playlist():
    try: 
        # get token info from session
        token_info = get_token()
    except:
        # if no token info, redirect user to login route
        print('User not logged in')
        return redirect("/login")

    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    # current user method returns a dictionary response, so we need to just grab the user id from it
    current_user_id = sp.current_user()['id']

    #first we need to make sure a playlist with same name doesn't exist already
    current_playlists =  sp.current_user_playlists()['items']
    existing_playlist_id = None
    for playlist in current_playlists:
        if(playlist['name'] == 'Weatherify'):
            existing_playlist_id = playlist['id']
    
    #create a playlist called Weatherify if that playlist doesn't exist already, and save its playlist id in existing_playlist_id
    if existing_playlist_id == None:
        existing_playlist_id=sp.user_playlist_create(current_user_id, 'Weatherify', public=True, collaborative=False, description='A playlist generated from the current weather at your location')['id']

    #now we need to gather songs, we want to add songs to our playlist
    song_uris = []
    #get top tracks
    top_tracks = sp.current_user_top_tracks(limit=20, offset=0, time_range='medium_term')['items']
    for song in top_tracks:
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!if it falls within our valence range add it, these are placeholders, we need to pass in a lower/upper bound/weather param and valence score
        #don't add if its a repeat
        if (song['uri'] not in song_uris):
            if (.85 <= sp.audio_features(song['id'])[0]['valence'] <= 1) :
                song_uri= song['uri']
                song_uris.append(song_uri)
            
    #loop over the user's playlists and within each playlist loop over songs and add them if they match valence req.
    for playlist in sp.current_user_playlists(limit=50, offset=0)['items']:
        playlist_id = playlist['id']

        for song in sp.playlist_items(playlist_id, fields=None, limit=15, offset=0, market=None, additional_types=('track', 'episode'))['items']:
            #don't add if its a repeat
            if (song['track']['uri'] not in song_uris):
                if (.85 <= sp.audio_features(song['track']['id'])[0]['valence'] <= 1) :
                    song_uri= song['track']['uri']
                    song_uris.append(song_uri)
    

    # add the songs to the playlist
    sp.user_playlist_add_tracks(current_user_id, existing_playlist_id, song_uris, None)
    


    # send them to the done html page and display their generated playlist
    playlist=[]

    #checking if we can access weather within this function
    return weather
    #return render_template("done.html", playlist=playlist)

def create_spotify_oauth():
    # ********NEED TO FIX, IS CAUSING ERRORS WITH TOKEN, FOR NOW IT ONLY
    #**********WORKS WHEN YOU DIRECTLY SET client_id, client_secret equal to their values
    # grabs the api key from the .env file and stores it in api_key
    return SpotifyOAuth(
        client_id = app.config['CLIENT_ID'],
        client_secret = app.config['CLIENT_SECRET'],
        redirect_uri = app.config['REDIRECT_URI'],
        scope = app.config['SCOPE']
    )

# function to get the token info from the session
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))
    
    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info

app.run(debug=True)

# if __name__ == "__main__":
#     app.run()