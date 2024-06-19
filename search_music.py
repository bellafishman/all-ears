import os
import json
import base64
import requests
import api_utils
import boto3

from configparser import ConfigParser

# Environment variables should be set in the Lambda console
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def lambda_handler(event, context):
    try:
        print("**STARTING**")

        #
        # We are expecting a token and type_info and :
        #
        print("**Accessing request body**")
        
        # Extract path parameters from the event
        path_parameters = event.get("pathParameters", {})
        type_info = path_parameters.get("type_param")
        query = path_parameters.get("filter_query")
        token = path_parameters.get("token")
        
        # Check if any of the path parameters are missing
        if not all([type_info, query, token]):
            return {
                'statusCode': 400,
                'body': json.dumps("Missing path parameters")
            }
            
        # Make the request to Spotify API with the provided token
        headers = {
            'Authorization': "Bearer " + token,
            'Content-Type': 'application/json'
        }
        
        print("** HEADERS:", headers)
        
        url = "https://api.spotify.com/v1/search"
        #
        # if type_info == artist, get artist's 20 top tracks
        #
        if type_info == "artist":
            url_info = f"?q={query}&type={type_info}&limit=1"
            
            query_url = url + url_info
            response = requests.get(query_url, headers=headers)
            data = response.json()
            
            # Check the status code of the response
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
                
            json_result = data["artists"]["items"]
            if len(json_result) == 0:
                return api_utils.error(400, "no artist found with given name")
                
            artist_info = json_result[0]
            artist_id = artist_info["id"]
            
            # now we can look up 20 top songs of artist
            url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
            response = requests.get(url, headers=headers)
            data = response.json()
            
            result = {}
            
            for track in data["tracks"]:
                track_name = track["name"]
                album_name = track["album"]["name"]
                artists = [artist["name"] for artist in track["artists"]]
                trackid = track["id"]
                
                result[track_name] = {"album": album_name, "artists": artists, "trackid": trackid}
            
            # Return the response from Spotify API
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
      
        # 
        # if type_info == genre, get genre's top 20 tracks
        #
        elif type_info == "genre":
            url = f"https://api.spotify.com/v1/recommendations?limit=20&market=US&seed_genres={query}"
            
            response = requests.get(url, headers=headers)
            data = response.json()
            
            # Check the status code of the response
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
                
            json_result = data["tracks"]
            
            if len(json_result) == 0:
                return api_utils.error(400, "no genre found")
            
            result = {}
                
            for track in json_result:
                track_name = track["name"]
                album_name = track["album"]["name"]
                artists = [artist["name"] for artist in track["artists"]]
                trackid = track["id"]
                
                result[track_name] = {"album": album_name, "artists": artists, "trackid": trackid}
            
                
            # Return the response from Spotify API
            return api_utils.success(200, result)
            
      
        #
        # if type_info == track, get top 5 matching tracks
        #
        elif type_info == "track":
            url = f"https://api.spotify.com/v1/search?q={query}&type=track&market=US&limit=5"
            
            response = requests.get(url, headers=headers)
            data = response.json()
            
            # Check the status code of the response
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
                
            json_result = data["tracks"]
            if len(json_result) == 0:
                return api_utils.error(400, "no tracks found")
                
            result = {}
                
            for track in json_result["items"]:
                track_name = track["name"]
                album_name = track["album"]["name"]
                artists = [artist["name"] for artist in track["artists"]]
                trackid = track["id"]
                
                result[track_name] = {"album": album_name, "artists": artists, "trackid": trackid}
                
            # Return the response from Spotify API
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
      
        # 
        # if type_info == album, list closest 5 albums
        #
        elif type_info == "album":
            url = f"https://api.spotify.com/v1/search?q={query}&type=album&market=US&limit=10"
            
            response = requests.get(url, headers=headers)
            data = response.json()
            
            # Check the status code of the response
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
                
            json_result = data["albums"]
            if len(json_result) == 0:
                return api_utils.error(400, "no tracks found")
                
            result = {}
                
            for album in json_result["items"]:
                track_name = album["name"]
                artists = [artist["name"] for artist in album["artists"]]
                trackid = album["id"]
                
                result[track_name] = {"artists": artists, "trackid": trackid} 
                
                
            # Return the response from Spotify API
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
      
        # Construct the Spotify API search URL
        url = f"https://api.spotify.com/v1/search?q={query}&type={type_info}"
        
        
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
            
        data = response.json()
    
        # Check the status code of the response
        if response.status_code != 200:
            if response.status_code == 401:
                return {
                    'statusCode': response.status_code,
                    'body': json.dumps({
                        'error': f"Spotify API has a bad or expired token"
                    })
                }
            if response.status_code == 403:
                return {
                    'statusCode': response.status_code,
                    'body': json.dumps({
                        'error': f"Spotify API has bad OAuth request"
                    })
                }
            return {
                'statusCode': response.status_code,
                'body': json.dumps({
                    'error': f"Spotify API error"
                })
            }
    
        # Return the response from Spotify API
        return {
            'statusCode': 200,
            'body': json.dumps(data)
        }

    
    except Exception as error:
        print("**ERROR**")
        print(str(error))
        return {
            'statusCode': 400,
            'body': json.dumps({
                "type": "error",
                "message": str(error)
            }),
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            }
        }

