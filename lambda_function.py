#
# Creates a rating of a song or album in
# MusicApp database.
#

import json
import boto3
import os
import datatier
import requests

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**lambda: user_stats_allears**")
    
    #
    # setup AWS based on config file:
    #
    config_file = 'musicapp-config.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
    
    #
    # configure for S3 access:
    #
    #s3_profile = 's3readonly'
    #boto3.setup_default_session(profile_name=s3_profile)
    #
    #bucketname = configur.get('s3', 'bucket_name')
    #
    #s3 = boto3.resource('s3')
    #bucket = s3.Bucket(bucketname)
    
    #
    # configure for RDS access
    #
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')

    #
    # userid from event: could be a parameter
    # or could be part of URL path ("pathParameters"):
    #
    print("**Accessing event/pathParameters**")
    
    # Extract path parameters from the event
    path_parameters = event.get("pathParameters", {})
    spotify_token = path_parameters.get("spotify_token")
    
    if not spotify_token:
      return {
        'statusCode': 400,
        'body': json.dumps("error: no spotify token give")
      }


    #
    # open connection to the database:
    #
    print("**Opening connection**")
    
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    
    #
    # get authentication token from request headers:
    #
    print("**Accessing request headers to get authenticated user info")
    
    if "headers" not in event:
      msg = "no headers in request"
      print("**ERROR:", msg)
      return {
        'statusCode': 400,
        'body': json.dumps(msg)
      }
    
    headers = event["headers"]
      
    if "Authentication" not in headers:
      msg = "no security credentials"
      print("**ERROR:", msg)
      return {
        'statusCode': 401,
        'body': json.dumps(headers)
      }
    
    token = headers['Authentication']
    
    
    #
    # is the token valid? Ask the authentication service...
    #
    auth_url = configur.get('auth', 'webservice')
    data = {"token": token}
    
    api = '/auth'
    url = auth_url + api
    
    response = requests.post(url, json=data)
    
    if response.status_code != 200:
      msg = "authentication failure"
      print("**ERROR:", msg)
      return {
        'statusCode': 401,
        'body': json.dumps(msg)
      }
    
    
    
    #
    # retrieve userid from tokens
    #
    user_sql = "SELECT userid FROM tokens WHERE token = %s"
    user_info = datatier.retrieve_one_row(dbConn, user_sql, token)
    userid = user_info[0]
    
    
    #
    # now retrieve all the user ratings:
    #
    sql = """ SELECT * FROM ratings WHERE userid = %s ORDER BY num_stars DESC"""

    rows = datatier.retrieve_all_rows(dbConn, sql, userid)
    if not rows:
      msg = "user has not ratings"
      print(msg)
      return {
        'statusCode': 200,
        'body': json.dumps(msg)
      }
    print(rows)
    
    stats = {}
    
    # Calculate average rating
    total_stars = sum(row[3] for row in rows)
    average_rating = total_stars / len(rows)
    stats['average_rating'] = average_rating
    
        
    # get top artists and top genres:
    
    # Make the request to Spotify API with the provided token
    headers = {
        'Authorization': "Bearer " + spotify_token,
        'Content-Type': 'application/json'
    }
    
    
    # Aggregate data for highest-rated albums, tracks, artists, and genres
    albums = {}
    artists = {}
    genres = {}
    tracks = {}

    for row in rows:
        musicid = row[2]

        # Get track details
        url = f"https://api.spotify.com/v1/tracks/{musicid}"
        response = requests.get(url, headers=headers)
        data = response.json()

        if response.status_code != 200:
            # Maybe an album?
            url = f"https://api.spotify.com/v1/albums/{musicid}"
            response = requests.get(url, headers=headers)
            data = response.json()
            
            # fail!
            if response.status_code != 200:
                if response.status_code == 401:
                    return {
                        'statusCode': response.status_code,
                        'body': json.dumps("error: Spotify API has a bad or expired token")
                    }
                if response.status_code == 403:
                    return {
                        'statusCode': response.status_code,
                        'body': json.dumps("error: Spotify API has bad OAuth request")
                    }
                return {
                    'statusCode': response.status_code,
                    'body': json.dumps("error: Spotify API error")
                }
            album_name = data['name']
            albums[album_name] = albums.get(album_name, 0) + int(row[3])
            for artist in data['artists']:
              artist_name = artist['name']
              artists[artist_name] = artists.get(artist_name, 0) + int(row[3])
              
            if 'genres' in data:
                for genre in data['genres']:
                    genres[genre] = genres.get(genre, 0) + int(row[3])
        
        else:
          track_name = data['name']
          tracks[track_name] = tracks.get(track_name, 0) + int(row[3])
          album_name = data['album']['name']
          albums[album_name] = albums.get(album_name, 0) + int(row[3])
          for artist in data['artists']:
            artist_name = artist['name']
            artists[artist_name] = artists.get(artist_name, 0) + int(row[3])
            
          album_id = data['album']['id']
          # Get album to get album genres
          url = f"https://api.spotify.com/v1/albums/{album_id}"

          response = requests.get(url, headers=headers)
          album_data = response.json()
          if 'genres' in album_data:
              for genre in album_data['genres']:
                  genres[genre] = genres.get(genre, 0) + int(row[3])

    
    
    
    # Sort and get top-5-rated albums, artists, and genres
    stats['top_albums'] = sorted(albums.items(), key=lambda x: x[1], reverse=True)[:5]
    stats['top_artists'] = sorted(artists.items(), key=lambda x: x[1], reverse=True)[:5]
    stats['top_genres'] = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:5]
    stats['top_tracks'] = sorted(tracks.items(), key=lambda x: x[1], reverse=True)[:5]

    
    
    #
    # respond in an HTTP-like way, i.e. with a status
    # code and body in JSON format:
    #
    print("**DONE, returning dictionary stats**")
    
    return {
      'statusCode': 200,
      'body': json.dumps(stats)
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 400,
      'body': json.dumps(str(err))
    }
