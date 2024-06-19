#
# Gets all of a user's rating's from
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
    
    print("**get_folders**")
    
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
    # now get user's' rating:
    #
    print("**Retrieving data**")


    sql = "SELECT * FROM folders WHERE userid = %s"

    rows = datatier.retrieve_all_rows(dbConn, sql, userid)
    
        
    
    #
    # respond in an HTTP-like way, i.e. with a status
    # code and body in JSON format:
    #
    print("**DONE, returning rows**")
    
    return {
      'statusCode': 200,
      'body': json.dumps(rows)
    }
    
  except Exception as err:
    print("**ERROR**")
    print(str(err))
    
    return {
      'statusCode': 400,
      'body': json.dumps(str(err))
    }
