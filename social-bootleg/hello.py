from flask import Flask, jsonify, request
from instagramy import *
from instaloader.structures import TopSearchResults
from instascrape import *
from selenium.webdriver import Chrome
import instaloader
import json
from instaloader.exceptions import PrivateProfileNotFollowedException, ProfileNotExistsException
import instascrape
app = Flask(__name__)
user = "" # to change profile that is checked by the app, user will have to get back to homepage
L = instaloader.Instaloader()
session_id = "50206634772%3A1ejDURc3jLJAYp%3A8" # to be loaded from JSON
headers = {
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.57",
    "cookie": "sessionid=50206634772%3A1ejDURc3jLJAYp%3A8;"
  }

def getContext():
    configFile = open('./social-bootleg/loginConfiguration.json')
    config = json.load(configFile)
    
    try:
        L.load_session_from_file(config['username'])
    except FileNotFoundError:
        L.login(config['username'], config['password'])
        L.save_session_to_file()
    
    return L.context

def getContextWithoutLogging():
  L = instaloader.Instaloader()
  return L.context

# used to process requests for most methods, which require only username to access data
def process_username_json(requestToProcess):
  content_type = requestToProcess.headers.get('Content-Type')
  if (content_type == 'application/json'):
    userData = json.dumps(requestToProcess.json)
  else:
    return 'Invalid data provided, a JSON is necessary', 502
  username = json.loads(userData)
  name = username['username']
  return name

@app.route("/", methods=['POST'])
def hello_world():
  username = process_username_json(request)
  user = Profile(username)
  user.scrape(headers=headers)
  user_basic_data = {
    "name" : f"{user.full_name}",
    "following" : f"{user.following}",
    "followers" : f"{user.followers}"
  }
  return jsonify(user_basic_data)

@app.route("/profile")
def profile():
  webdriver = Chrome()
  
  profile = Profile(user)
  profile.scrape(headers=headers)
  return f'{profile.followers}'

@app.route("/hashtags")
def hashtag_count():
  # h = Hashtag("cat")
  # h.scrape(headers=headers)
  tagname = 'cat'
  context = getContext()
  results = TopSearchResults(context, tagname) 
  related_tags = list(results.get_hashtags())
  for i in range(0,5):
    for tag in related_tags:
      results = TopSearchResults(context, tag.name)
      related_tags.append() 
  tag_names = []
  for tag in related_tags:
   tag_names.append(tag.name)
  
  return jsonify(tag_names)
  

@app.route("/engagement", methods=['POST'])
def get_engagement():
  username = process_username_json(request)
  webdriver = Chrome()
  profile = Profile(username)
  profile.scrape(headers=headers)
  followers_count = profile.followers
  posts = profile.get_posts(webdriver=webdriver, login_first=False)
  scraped, unscraped = scrape_posts(posts, silent=False, headers=headers, pause=7)
  
  likes = 0
  comments = 0
  for post in scraped:
    likes = likes + post.likes
    comments = comments + post.comments
  
  engagement = (likes+comments)/followers_count
  engagement_rate = {
    "engagement" : f'{engagement}'
  }
  return jsonify(engagement_rate)


@app.route("/similar_hashtags", methods=['POST'])
def get_similar_hashtags():
  context = getContextWithoutLogging()

@app.route("/likes/<user>")
def get_likes(user):
  context = getContext()
  instaloader.Hashtag.from_name(context, 'cat').get_posts()
  try:
    instaloader.Hashtag.from_name(context, 'cat').get_posts()
  except:
    return "No profile found"
  return user;

@app.route("/mostlikedposts/<user>")
def get_most_liked_posts(user):
    USER = user
    PROFILE = USER
    profile = instaloader.Profile.from_username(getContext(), PROFILE)
    posts_sorted_by_likes = sorted(profile.get_posts(),
                               key=lambda p: p.likes + p.comments,
                               reverse=True)

    return user;

@app.route("/ghostfollowers")
def get_ghost_followers():
    user = "sweet__potat"
    try:
      profile = instaloader.Profile.from_username(getContext(), user)
    except ProfileNotExistsException:
      return "No profile found"
    except PrivateProfileNotFollowedException:
      return "You cannot trace private profiles"
    likes = set()
    for post in profile.get_posts():
        likes = likes | set(post.get_likes())

    followers = set(profile.get_followers())
    ghosts = list(followers - likes)
    return json(ghosts)

@app.route("/ghostfollowers")
def get_ghost_followers1():
    user = "sweet__potat"
    webdriver = Chrome()
    headers = {
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.57",
    "cookie": "sessionid=50206634772%3A1ejDURc3jLJAYp%3A8;"
    }
    user = Profile("sweet__potat")
    user.scrape(headers=headers)
    
    posts = user.get_posts(webdriver=webdriver, login_first=True)
    try:
      profile = instaloader.Profile.from_username(getContext(), user)
    except ProfileNotExistsException:
      return "No profile found"
    except PrivateProfileNotFollowedException:
      return "You cannot trace private profiles"
    likes = set()
    for post in profile.get_posts():
        likes = likes | set(post.get_likes())

    followers = set(profile.get_followers())
    ghosts = list(followers - likes)
    return json(ghosts)

@app.route("/nofollowback", methods=['POST'])
def notFollowingBack():
  username = process_username_json(request)
  context = getContext()
  try:
    profile = instaloader.Profile.from_username(context, username)
  except ProfileNotExistsException:
    return user, 404
  except PrivateProfileNotFollowedException:
    return "You cannot trace private profiles", 401
  followers = set(profile.get_followers())
  followees = set(profile.get_followees())
  not_following_back = list(followers - followees)

  return jsonify(not_following_back)

