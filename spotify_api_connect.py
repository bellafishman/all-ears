import os
import json
import base64
import requests

# Environment variables should be set in the Lambda console
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def lambda_handler(event, context):
    try:
        print("**STARTING**")
        
        # Extract query string parameters if needed
        query_string_parameters = event.get('queryStringParameters', {})
        print("Query String Parameters:", query_string_parameters)
        
        # Retrieve access token from Spotify API
        access_token = get_access_token()
        if access_token:
            print("new token received")
            # Call the search function or any other function using the access token
            search(access_token)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    "type": "success",
                    "access_token": access_token
                }),
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                }
            }
        else:
            raise Exception("Failed to obtain access token")
    
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

def get_access_token():
    url = 'https://accounts.spotify.com/api/token'
    encoded = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    print("encoded =", encoded)

    headers = {
        "Authorization": f"Basic {encoded}",
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials'
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        json_response = response.json()
        print(json.dumps(json_response, indent=2))
        return json_response.get('access_token')
    except requests.RequestException as e:
        print(f"HTTP request failed: {e}")
        return None

def search(access_token):
    # Implement your search functionality here
    # For example, print the access token or use it in another API request
    print(f"Access Token: {access_token}")
