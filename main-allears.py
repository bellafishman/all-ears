#
# Client-side python app for musicapp.
#
# Authors:
#   << Bella Fishman >>

import requests
import jsons

import uuid
import pathlib
import logging
import sys
import os
import base64

from configparser import ConfigParser
from getpass import getpass


############################################################
#
# classes
#
class User:

  def __init__(self, row):
    self.userid = row[0]
    self.username = row[1]
    self.pwdhash = row[2]


class Job:

  def __init__(self, row):
    self.jobid = row[0]
    self.userid = row[1]
    self.status = row[2]
    self.originaldatafile = row[3]
    self.datafilekey = row[4]
    self.resultsfilekey = row[5]


############################################################
#
# prompt
#
def prompt():
  """
  Prompts the user and returns the command number

  Parameters
  ----------
  None

  Returns
  -------
  Command number entered by user (0, 1, 2, ...)
  """
  print()
  print(">> Enter a command:")
  print("   0 => end *")
  print("   1 => users *")
  print("   2 => create a rating *")
  print("   3 => create a folder *")
  print("   4 => search *")
  print("   5 => get my ratings *")
  print("   6 => get my folders *")
  print("   7 => add to folder *")
  print("   8 => open folder *")
  print("   9 => user stats *")
  print("   10 => new user? *")
  print("   11 => login *")
  print("   12 => authenticate token *")
  print("   13 => logout")

  cmd = input()

  if cmd == "":
    cmd = -1
  elif not cmd.isnumeric():
    cmd = -1
  else:
    cmd = int(cmd)

  return cmd


############################################################
#
# users
#
def users(baseurl):
  """
  Prints out all the users in the database

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    api = '/get_users'
    url = baseurl + api

    res = requests.get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # deserialize and extract users:
    #
    body = res.json()

    #
    # let's map each row into a User object:
    #
    users = []
    for row in body:
      user = User(row)
      users.append(user)
    #
    # Now we can think OOP:
    #
    if len(users) == 0:
      print("no users...")
      return

    for user in users:
      print(user.userid)
      print(" ", user.username)
      print(" ", user.pwdhash)
    #
    return

  except Exception as e:
    logging.error("users() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return



############################################################
#
# create_rating
#
def create_rating(baseurl, token, musicid=None):
  """
  Prints out an authenticated user's folder contents

  Parameters
  ----------
  baseurl: baseurl for web service
  token: user authentication token
  music: Spotify API track id

  Returns
  -------
  nothing
  """
  if musicid is None:
    print("Give the musicid>")
    musicid = input()

  print("Provide your rating /5 Stars!")
  while True:
    num_stars = input()
    if not num_stars.isnumeric():
      num_stars = -1

    num_stars = int(num_stars)
    if num_stars < 0 or num_stars > 5:
      print("Invalid Number of Stars!")
    else:
      break
  print("What were your thoughts on the music?")
  comment = input()
  
  try:

    # ensure we got a token
    if token is None:
      print("No current token, please login")
      return

    #
    # call the web service:
    #
    api = '/create_rating'
    url = baseurl + api + '/' + token

    #
    # make request:
    #

    # if there is a token, it needs to be passed in the
    # header of /POST 
    data = {"musicid":musicid, "num_stars":num_stars, "comment":comment}
    res = requests.post(url, json=data)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      if res.status_code == 401:
        body = res.json()
        print(body)
        return
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print(body)
        return
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      #
      return

    print("Success! You've reviewed some music!")
    
    return

  except Exception as e:
    logging.error("jobs() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return



############################################################
#
# create_rating
#
def create_folder(baseurl, token):
  """
  Creates an empty user folder

  Parameters
  ----------
  baseurl: baseurl for web service
  token: user authentication token

  Returns
  -------
  folderid or None if error
  """
  
  # ensure we got a token
  if token is None:
    print("No current token, please login")
    return
    
  print("Give this folder a name>")
  folder_name = input()

  try:
    #
    # call the web service:
    #
    api = '/create_folder'
    url = baseurl + api

    #
    # make request:
    #

    # if there is a token, it needs to be passed in the
    # header of /POST 
    data = {"folder_name":folder_name, "token":token}
    res = requests.post(url, json=data)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      if res.status_code == 401:
        body = res.json()
        print(body)
        return
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print(body)
        return
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      #
      return

    print("Success! You've made a new folder!")
    body = res.json()
    return body

  except Exception as e:
    logging.error("create_folder() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return



  
############################################################
#
# search
#
def search(baseurl, spotify_token):
  """
  Prompts the user for a type and a search parameter, 
  and searchs Spotify API for matching songs. From here 
  you can select a song to perform either nothing,     
  create_rating, or add_to_folder

  Parameters
  ----------
  baseurl: baseurl for web service
  spotify_token: Spotify API token

  Returns
  -------
  nothing
  """
  print( "Provide a type to filter by (ex: 'artist', 'track', 'album', 'genre')>")
  type_param = input()
  print()
  print("Provide a search (ex: 'Steely Dan', 'Dirty Work', 'rock')")
  filter_query = input()

  try:
    #
    # call the web service:
    #
    #req_header = {"token": spotify_token}

    
    api = '/search'
    url = baseurl + api + '/' + type_param + '/' + filter_query + '/' + spotify_token
    
    # get request
    res = requests.get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # success, extract track information:
    #
    body = res.json()

    
    track_list = {}
    for index, (track, info) in enumerate(body.items(), start=1):
      print(f"{index}. {track}")
      if "album" in info:
        print(f"    Album: {info['album']}")
      print(f"    Artist: {','.join(info['artists'])}")
      print()
      track_list[index] = info['trackid']

    
    print(
      '''Supply an track index from above to write a track rating or add to a folder (or press enter to exit)>
      ''')
    while True:
      track_index = input()
      if track_index == "":
        return
      elif not track_index.isnumeric():
        track_index = -1
      track_index = int(track_index)
      if track_index < 1 or track_index > len(track_list):
        print("Invalid Track index")
      
      else:
        break
    print()
    print("1 => Rate track")
    print("2 => Add to folder")
    while True:
      option = input("Choose an option: ")
      if option == "":
        return
      elif not option.isnumeric():
        option = -1
      option = int(option)
      if option != 1 and option != 2:
        print("Invalid Option")
      else: break

    if option == 1:
      create_rating(baseurl, token, track_list[track_index])
    elif option == 2:
      add_to_folder(baseurl, token, track_list[track_index])

        ### add content here for function
      
    

    return

  except Exception as e:
    logging.error("upload() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return



############################################################
#
# get_ratings
#
def get_ratings(baseurl, token, spotify_token):
  """
  Prints out a user's ratings

  Parameters
  ----------
  baseurl: baseurl for web service
  token: user specific and time-outable token
  spotify_token: Spotify API token

  Returns
  -------
  nothing
  """
  try:

    # ensure we got a token
    if token is None or spotify_token is None:
      print("No current token, please login")
      return
      

    #
    # call the web service:
    #
    api = '/get_ratings'
    url = baseurl + api + '/' + spotify_token

    #
    # make request:
    #

    # if there is a token, it needs to be passed in the 
    # header of /GET jobs
    req_headers = {"Authentication": token}
    res = requests.get(url, headers=req_headers)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      if res.status_code == 401:
        body = res.json()
        print(body)
        return
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print(body)
        return
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      #
      return
    #
    # deserialize and extract jobs:
    #
    body = res.json()
    #
    # printing in a nice way:
    #
    print("Ratings:   ")

    if not body:
      print("no ratings...")
      return

    for index, (ratingid, info) in enumerate(body.items(), start=1):
      if "track_name" in info:
          print(f"{index}. {info['track_name']}")
      elif "album" in info:
          print(f"{index}. {info['album']}")  # In case there's no track name, print the trackid
      if "album" in info:
        print(f"    Album: {info['album']}")

      print(f"    Artist: {', '.join(info['artists'])}")
      print(f"    Stars: {info['num_stars']}")
      print(f"    Comment: {info['comment']}")
      print()
    #
    return

  except Exception as e:
    logging.error("get ratings failed:")
    logging.error("url: " + url)
    logging.error(e)
    return

############################################################
#
# get_folders
#
def get_folders(baseurl, token):
  """
  Prints out an authenticated user's folder contents

  Parameters
  ----------
  baseurl: baseurl for web service
  token: user authentication token

  Returns
  -------
  dictionary of indices and folder ids
  """
  try:

    # ensure we got a token
    if token is None:
      print("No current token, please login")
      return

    #
    # call the web service:
    #
    api = '/get_folders'
    url = baseurl + api

    #
    # make request:
    #

    # if there is a token, it needs to be passed in the
    # header of /GET jobs
    req_header = {"Authentication": token}
    res = requests.get(url, headers=req_header)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      if res.status_code == 401:
        body = res.json()
        print(body)
        return
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print(body)
        return
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      #
      return
    #
    # deserialize and extract jobs:
    #
    body = res.json()

    if not body:
      print("no folders...")
      return
    
    # printing and tracking ids
    print("Folders:")
    folder_id = {}
    for index, row in enumerate(body, start=1):
      print(f"{index}. {row[2]}")
      print()
      folder_id[index] = row[0]
    

    #
    # return dict for later use
    #
    #
    return folder_id

  except Exception as e:
    logging.error("get_folders() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return



############################################################
#
# add_to_folder
#
def add_to_folder(baseurl, token, musicid=None):
  """
  Adds a singular song or album to a folder

  Parameters
  ----------
  baseurl: baseurl for web service
  token: user authentication token
  musicid: Spotify id

  Returns
  -------
  nothing
  """
  # ensure we got a token
  if token is None:
    print("No current token, please login")
    return
  
  if musicid is None:
    print("Give the musicid>")
    musicid = input()
  if musicid == "":
    print("bad input")
    return
    
  print("What folder to add to?")
  folder_dict = get_folders(baseurl, token)
  if folder_dict is None:
    folder_len = 0
    print("1.  Add New Folder")
  else:
    folder_len = len(folder_dict)
    print(f"{folder_len + 1}. Add new folder")
  print("Input folder index to add to: ")
  folder_index = input()
  if folder_index == "":
    return
  elif not folder_index.isnumeric():
    folder_index = -1
  folder_index = int(folder_index)
  if folder_index < 1 or folder_index > (folder_len + 1):
    print("Invalid Folder index")
    return
    
  ## Add a new folder:
  if folder_index ==  (folder_len + 1):
    folder_id = create_folder(baseurl, token)
  
  else:
    folder_id = folder_dict[folder_index]
  
  try:

    #
    # call the web service:
    #
    api = '/add_to_folder'
    url = baseurl + api

    #
    # make request:
    #

    # if there is a token, it needs to be passed in the
    # header of /POST 
    data = {"musicid":musicid, "token":token, "folderid":folder_id}
    res = requests.post(url, json=data)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      if res.status_code == 401:
        body = res.json()
        print(body)
        return
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print(body)
        return
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      #
      return

    print("Success! You've added a song to your folder!")

    return

  except Exception as e:
    logging.error("add_to_folder() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
#
# open_folder
#
def open_folder(baseurl, token, spotify_token, folderid=None):
  """
  Opens a folder to view contents

  Parameters
  ----------
  baseurl: baseurl for web service
  token: user authentication token
  spotify_token: Spotify API token
  folderid: folder id

  Returns
  -------
  folder_contents dictionary to be later possibly used to edit or delete folder contents
  None if error
  """
  
  
  try:
    # ensure we got a token
    if token is None:
      print("No current token, please login")
      return

    if folderid is None:
      print("What folder to open?")
      folder_dict = get_folders(baseurl, token)
      print("Input folder index to open: ")
      folder_index = input()
      if folder_index == "":
        return
      elif not folder_index.isnumeric():
        folder_index = -1
      folder_index = int(folder_index)
      if folder_index < 1 or folder_index > len(folder_dict):
        print("Invalid Folder index")
        return

      folderid = folder_dict[folder_index]
    else: 
      None
    

    #
    # make request:
    #

    # if there is a token, it needs to be passed in the
    # header of /GET 
    header = {"Authentication":token}
    #
    # call the web service:
    #
    print(folderid)
    api = '/open_folder'
    url = baseurl + api + '/' + spotify_token + '/' + str(folderid)
    res = requests.get(url, headers=header)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      if res.status_code == 401:
        body = res.json()
        print(body)
        return
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print(body)
        return
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      #
      return


    body = res.json()

    if not body:
      print("no ratings...")
      return
  
    folder_contents = {}
    for index, info in body.items():
      if "track_name" in info:
        print(f"{index}. {info['track_name']}")
      elif "album" in info:
        print(f"Album: {info['album']}")
      if "album" in info:
        print(f"    Album: {info['album']}")
      print(f"    Artist: {','.join(info['artists'])}")
      print()
      folder_contents[index] = info['trackid']

    return folder_contents

  except Exception as e:
    logging.error("open_folder() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return

############################################################
#
# user_stats
#
def user_stats(baseurl, token, spotify_token):
  """
  View personal user stats

  Parameters
  ----------
  baseurl: baseurl for web service
  token: user authentication token
  spotify_token: Spotify API token

  Returns
  -------
  None
  """


  try:
    # ensure we got a token
    if token is None:
      print("No current token, please login")
      return

    #
    # make request:
    #

    # if there is a token, it needs to be passed in the
    # header of /GET 
    header = {"Authentication":token}
    #
    # call the web service:
    #
    
    api = '/user_stats'
    url = baseurl + api + '/' + spotify_token
    res = requests.get(url, headers=header)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      if res.status_code == 401:
        body = res.json()
        print(body)
        return
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print(body)
        return
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      #
      return


    body = res.json()

    if not body:
      print("no ratings...")
      return
    print()
    print("Your User Ratings Stats:   ")
    print("Average Rating:  ", body["average_rating"])
    if body["top_genres"]:
      print("Top Genres:")
      for index, genre in enumerate(body["top_genres"], start=1):
        print(f"    {index}. {genre[0]}")
    if body["top_tracks"]:
      print("Top Tracks:")
      for index, track in enumerate(body["top_tracks"], start=1):
        print(f"    {index}. {track[0]}")
    if body["top_albums"]:
      print("Top Albums:") 
      for index, album in enumerate(body["top_albums"], start=1):
        print(f"    {index}. {album[0]}")
    if body["top_artists"]:
      print("Top Artists:")
      for index, artist in enumerate(body["top_artists"], start=1):
        print(f"    {index}. {artist[0]}")
    
    return 

  except Exception as e:
    logging.error("user_stats() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
#
# new_user
#
def new_user(baseurl):
  """
  Prompts the user for the email, username, password,
  first and last name to create a new user if email
  not already taken.

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  print("New User?")
  print("Enter email>")
  email = input()
  print("Enter your first name>")
  f_name = input()
  print("Enter your last name>")
  l_name = input()
  print("Enter a username>")
  username = input()
  
  while True:
    print("Enter a secure password>")
    password = input()
    print("Reenter the password>")
    password2 = input()
    if password != password2:
      print("Passwords don't match!")
    else:
      break
  if not email or not f_name or not l_name or not username or not password:
    print("input valid parameters")
    return
  try:

    data = {"username":username, "pwd":password, "first_name":f_name,
           "last_name":l_name, "email": email}
    #
    # call the web service:
    #
    api = '/put_user'
    url = baseurl + api

    res = requests.post(url, json=data)


    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      if res.status_code == 401:
        body = res.json()
        print(body)
        return
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print(body)
        return
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      #
      return

    body = res.json()
    print("User added successfully, userid: ", body)
    return

  except Exception as e:
    logging.error("put_user() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return



############################################################
#
# login
#
def login(baseurl):
  """
  Prompts the user for a username and password, then tries
  to log them in. If successful, returns the token returned
  by the authentication service. Also retreives a spotify_token
  for spotify API operations

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  token if successful, None if not
  spotify_token if successful, None if not
  """

  try:
    username = input("username: ")
    password = getpass()
    duration = input("# of minutes before expiration? ")

    #
    # build message:
    #
    data = {"username": username, "password": password, "duration": duration}

    #
    # call the web service to get token:
    #
    api = '/auth'
    url = baseurl + api

    res = requests.post(url, json=data)

    #
    # clear password variable:
    #
    password = None

    #
    # let's look at what we got back:
    #
    if res.status_code == 401:
      #
      # authentication failed:
      #
      body = res.json()
      print(body)
      return (None, None)

    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return (None, None)

    #
    # success, extract token:
    #
    body = res.json()

    token = body

    api_2 = '/access_token'
    url_2 = baseurl + api_2

    res_2 = requests.get(url_2)

    #
    # let's look at what we got back:
    #
    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return (None, None)

    #
    # deserialize and extract token:
    #
    body_2 = res_2.json()

    spotify_token = body_2["access_token"]

    print("logged in, token:", token)
    print("accessed api, token:", spotify_token)
    return (token, spotify_token)

  except Exception as e:
    logging.error("login() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return (None, None)


############################################################
#
# authenticate
#
def authenticate(baseurl, token):
  """
  Since tokens expire, this function authenticates the 
  current token to see if still valid. Outputs the result.

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    if token is None:
      print("No current token, please login")
      return

    print("token:", token)

    #
    # build message:
    #
    data = {"token": token}

    #
    # call the web service to upload the PDF:
    #
    api = '/auth'
    url = baseurl + api

    res = requests.post(url, json=data)

    #
    # let's look at what we got back:
    #
    if res.status_code == 401:
      #
      # authentication failed:
      #
      body = res.json()
      print(body)
      return

    if res.status_code != 200:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # success, token is valid:
    #
    print("token is valid!")
    return

  except Exception as e:
    logging.error("authenticate() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
# main
#
try:
  print('** All Ears: Music Rating and Sharing Platform **')
  print()

  # eliminate traceback so we just get error message:
  sys.tracebacklimit = 0

  #
  # what config file should we use for this session?
  #
  config_file = 'musicapp-client-config.ini'

  #
  # does config file exist?
  #
  if not pathlib.Path(config_file).is_file():
    print("**ERROR: config file '", config_file, "' does not exist, exiting")
    sys.exit(0)

  #
  # setup base URL to web service:
  #
  configur = ConfigParser()
  configur.read(config_file)
  baseurl = configur.get('client', 'webservice')

  #
  # make sure baseurl does not end with /, if so remove:
  #
  if len(baseurl) < 16:
    print("**ERROR: baseurl '", baseurl, "' is not nearly long enough...")
    sys.exit(0)

  if baseurl == "https://YOUR_GATEWAY_API.amazonaws.com":
    print("**ERROR: update config file with your gateway endpoint")
    sys.exit(0)

  if baseurl.startswith("http:"):
    print("**ERROR: your URL starts with 'http', it should start with 'https'")
    sys.exit(0)

  lastchar = baseurl[len(baseurl) - 1]
  if lastchar == "/":
    baseurl = baseurl[:-1]

  #
  # initialize login token:
  #
  token = None
  spotify_token = None

  #
  # main processing loop:
  #
  cmd = prompt()

  while cmd != 0:
    #
    # get_following
    # add_follow
    # within search
    # create_folder
    # add_to_folder

    if cmd == 1:
      users(baseurl)
    elif cmd == 2:
      create_rating(baseurl, token, musicid=None)
    elif cmd == 3:
      create_folder(baseurl, token)
    elif cmd == 4:
      search(baseurl, spotify_token)
    elif cmd == 5:
      get_ratings(baseurl, token, spotify_token)
    elif cmd == 6:
      get_folders(baseurl, token)
    elif cmd == 7:
      add_to_folder(baseurl, token, musicid=None)
    elif cmd == 8:
      open_folder(baseurl, token, spotify_token, folderid=None)
    elif cmd == 9:
      user_stats(baseurl, token, spotify_token)
    elif cmd == 10:
      new_user(baseurl)
    elif cmd == 11:
      # get spotify and rds token
      [token, spotify_token] = login(baseurl)
    elif cmd == 12:
      authenticate(baseurl, token)
      
    elif cmd == 13:
      #
      # logout
      #
      token = None
    else:
      print("** Unknown command, try again...")
    #
    cmd = prompt()

  #
  # done
  #
  print()
  print('** done **')
  sys.exit(0)

except Exception as e:
  logging.error("**ERROR: main() failed:")
  logging.error(e)
  sys.exit(0)
