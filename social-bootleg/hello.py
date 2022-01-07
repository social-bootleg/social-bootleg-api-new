from os import linesep
from flask import Flask, jsonify, request, session
from flask_session import Session
import instagramy
from instaloader.structures import TopSearchResults
from instascrape import *
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import instaloader
import json
from instaloader.exceptions import PrivateProfileNotFollowedException, ProfileNotExistsException

app = Flask(__name__)
app.secret_key = 'secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config.from_object(__name__)

sess = Session()
sess.init_app(app)
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
def process_json_from_enduser(requestToProcess, toExtract):
  content_type = requestToProcess.headers.get('Content-Type')
  if (content_type == 'application/json'):
    userData = json.dumps(requestToProcess.json)
  else:
    return 'Invalid data provided, a JSON is necessary', 502
  data = json.loads(userData)
  extracted = data[f'{toExtract}']
  return extracted

# for performance reasons, this site must be accessed at start of browsing the front-end!!!
@app.route("/", methods=['POST'])
def hello_world():
  username = process_json_from_enduser(request, 'username')
  user = Profile(username)
  user.scrape(headers=headers)
  user_basic_data = {
    "name" : f"{user.full_name}",
    "following" : f"{user.following}",
    "followers" : f"{user.followers}"
  }

  # save data for further processing
  profile = instaloader.Profile.from_username(getContext(), username)
  all_posts = profile.get_posts()
  posts = []
  for post in all_posts:
    posts.append(post)
  session['posts'] = posts
  return jsonify(user_basic_data)

@app.route("/engagement", methods=['POST'])
def get_engagement():
  username = process_json_from_enduser(request, 'username')
  profile = Profile(username)
  profile.scrape(headers=headers)
  followers_count = profile.followers
  posts = session.get('posts',profile.get_recent_posts())
  
  likes = 0
  comments = 0
  for post in posts:
    likes = likes + post.likes
    comments = comments + post.comments
  
  engagement = (likes+comments)/followers_count
  engagement_rate = {
    "likes" : f'{likes}',
    "comments" : f'{comments}',
    "engagement" : f'{engagement}'
  }
  return jsonify(engagement_rate)

@app.route("/mostlikedposts", methods=['POST'])
def get_most_liked_posts():
    PROFILE = process_json_from_enduser(request, 'username')
    most_liked = []
    profile = instaloader.Profile.from_username(getContext(), PROFILE)
    posts = session.get('posts',profile.get_posts())
    posts_sorted_by_likes = sorted(posts,
                               key=lambda p: p.likes + p.comments,
                               reverse=True)
    if (len(posts_sorted_by_likes)>10):
      posts_sorted_by_likes = posts_sorted_by_likes[:10]
    
    for post in posts_sorted_by_likes:
      most_liked.append({"picture_url": f'{post.url}', "likes" : f'{post.likes}', "comments" : f'{post.comments}'})
    return jsonify(most_liked);

# it's not working!
@app.route("/ghostfollowers")
def get_ghost_followers():
    user = "sweet__potat"
    try:
      profile = instaloader.Profile.from_username(getContext(), user)
    except ProfileNotExistsException:
      return "No profile found"
    except PrivateProfileNotFollowedException:
      return "You cannot trace private profiles"
    time.sleep(0.5)
    likes = set()
    for post in profile.get_posts():
        likes = likes | set(post.get_likes())
        time.sleep(1)

    followers = set(profile.get_followers())
    ghosts = list(followers - likes)
    return json(ghosts)

# it's not working!
@app.route("/nofollowback", methods=['POST'])
def notFollowingBack():
  username = process_json_from_enduser(request)
  context = getContext()
  try:
    profile = instaloader.Profile.from_username(context, username)
  except ProfileNotExistsException:
    return username, 404
  except PrivateProfileNotFollowedException:
    return "You cannot trace private profiles", 401
  
  followers = set(profile.get_followers())
  followees = set(profile.get_followees())
  not_following_back = list(followers - followees)

  return jsonify(not_following_back)


@app.route("/related_tags", methods = ['POST'])
def related_tags():
  tag = process_json_from_enduser(request, 'hashtag')
  options = Options()
  options.headless = True
  driver = Chrome(options=options)
  driver.get("https://www.all-hashtag.com/hashtag-generator.php")
  input = driver.find_element_by_css_selector("input[name='keyword'")
  input.send_keys(tag)
  driver.find_element_by_class_name("btn-gen").click()
  tags_text = driver.find_element_by_class_name("copy-hashtags").get_attribute('innerHTML')
  tags = tags_text.split(' ')
  tags[:] = [x for x in tags if x]
  return jsonify(tags)

@app.route("/posts_stats")
def get_posts_stats():
  pass

@app.route("/unanswered_comments")
def get_unaswered_comments():
  username = "sweet__potat"
  profile = instaloader.Profile.from_username(getContext(), username)
  time.sleep(0.5)
  posts = profile.get_posts()
  time.sleep(0.5)
  for post in posts:
    post.get_comments()
    time.sleep(0.3)

  return '0'
