#
# Adds a song or album to a folder
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
    print("**lambda: proj03_users**")
    
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
    # the user has sent us 2 parameters:
    #  1. token
    #  2. folder_id
    #  3. music_id
    #
    # The parameters are coming through web server 
    # (or API Gateway) in the body of the request
    # in JSON format.
    #
    print("**Accessing request body**")
    
    if "body" not in event:
      raise Exception("event has no body")
      
    body = json.loads(event["body"]) # parse the json
    
    if "token" not in body:
      raise Exception("event has a body but no token")
      
    if "folderid" not in body:
      raise Exception("event has a body but no folder id")
    if "musicid" not in body:
      raise Exception("event has a body but no music id")

    token = body["token"]
    folderid = body["folderid"]
    musicid = body["musicid"]
    
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
    # now retrieve all the users:
    #
    print("**Retrieving data**")

    #
    # insert into folder_music
    #
    sql = """
          INSERT INTO folder_music (folderid, musicid)
          VALUES (%s, %s)
          """
    folder_info = [folderid, musicid]
    
    modified = datatier.perform_action(dbConn, sql, folder_info)
    
    if modified != 1:
      print("**INTERNAL ERROR: insert into database failed...**")
      return api_utils.error(400, "INTERNAL ERROR: insert failed to modify database")
    
    #
    # respond in an HTTP-like way, i.e. with a status
    # code and body in JSON format:
    #
    print("**DONE, returning success**")
    
    return {
      'statusCode': 200,
      'body': json.dumps({"message": "Music added to folder successfully"})
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 400,
      'body': json.dumps(str(err))
    }
