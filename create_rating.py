#
# Creates a rating of a song or album in
# MusicApp database.
#

import json
import boto3
import os
import datatier
import requests
import api_utils

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**create_rating**")
    
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
    # get authentication token from request headers:
    #
    print("**Accessing path parameters to get authenticated user info")
    
    # Extract path parameters from the event
    path_parameters = event.get("pathParameters", {})
    token = path_parameters.get("token")
    
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
      return api_utils.error(401, msg)
    
      

    #
    # the user has sent us 3 parameters:
    #  1. musicid
    #  2. num_stars
    #  3. comment
    #
    # The parameters are coming through web server 
    # (or API Gateway) in the body of the request
    # in JSON format.
    #
    print("**Accessing request body**")
    
    if "body" not in event:
      raise Exception("event has no body")
      
    body = json.loads(event["body"]) # parse the json
    
    if "musicid" not in body:
      raise Exception("event has a body but no musicid")
    
    # num stars not neccessary?
    # bc could be 0 stars ??
    num_stars = "0"
    comment = ""
    # comment is not necessary
    musicid = body["musicid"]
    if "num_stars" in body:
      num_stars = body["num_stars"]
      
    if "comment" in body:
      comment = body["comment"]
    

    #
    # open connection to the database:
    #
    print("**Opening connection**")
    
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    
    #
    # retrieve userid from tokens
    #
    user_sql = "SELECT userid FROM tokens WHERE token = %s"
    user_info = datatier.retrieve_one_row(dbConn, user_sql, token)
    userid = user_info[0]
    
    
    #
    # now insert rating:
    #
    print("**Retrieving data**")

    #
    # insert ratings into authenticated users userid in ratings table
    #
    sql = """
          INSERT INTO ratings (userid, musicid, num_stars, comment)
          VALUES (%s, %s, %s, %s)
          """
    rating_info = [userid, musicid, num_stars, comment]

    modified = datatier.perform_action(dbConn, sql, rating_info)

    if modified != 1:
      print("**INTERNAL ERROR: insert into database failed...**")
      return api_utils.error(400, "INTERNAL ERROR: insert failed to modify database")
    
    #
    # respond in an HTTP-like way, i.e. with a status
    # code and body in JSON format:
    #
    print("**DONE, returning**")
    
    return {
      'statusCode': 200,
      'body': json.dumps({"message": "Rating added successfully"})
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 400,
      'body': json.dumps(str(err))
    }
