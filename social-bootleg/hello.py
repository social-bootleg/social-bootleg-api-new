from os import linesep
import os
import sys
from uuid import UUID, uuid4
import uuid
from flask import Flask, jsonify, request, session, send_from_directory
from flask_session import Session
import operator
from instaloader.structures import TopSearchResults
from instascrape import *
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import instaloader
import json
from instaloader.exceptions import ConnectionException, PrivateProfileNotFollowedException, ProfileNotExistsException
from flask_cors import CORS, cross_origin
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
app.secret_key = 'secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config.from_object(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
sess = Session()
sess.init_app(app)
L = instaloader.Instaloader()

session_id = json.load(open('./social-bootleg/session_token.json'))['token'] # to be loaded from JSON
headers = {
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.57",
    "cookie": f"sessionid={session_id};"
  }

def getContext():
    configFile = open('./social-bootleg/loginConfiguration.json')
    config = json.load(configFile)
    L.login(config['username'], config['password'])
    time.sleep(0.7)
    
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

@app.route("/")
def hello_world():
  return 'Welcome to social-bootleg! \r\nEnter your Instagram username to get started.'

# for performance reasons, this site must be accessed at start of browsing the front-end!!!
@app.route("/", methods=['POST'])
def get_basic_data():
  username = process_json_from_enduser(request, 'username')
  user = Profile(username)
  user.scrape(headers=headers)
  full_name = user.full_name if user.full_name != "" else username
  user_basic_data = {
    "name" : f"{full_name}",
    "following" : f"{user.following}",
    "followers" : f"{user.followers}"
  }
  session['simple_profile'] = user
  # save data for further processing
  profile = instaloader.Profile.from_username(getContext(), username)
  all_posts = profile.get_posts()
  posts = []
  for post in all_posts:
    posts.append(post)
  session['profile'] = profile
  session['posts'] = posts
  return jsonify(user_basic_data)

@app.route("/engagement", methods=['POST'])
@cross_origin()
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
    profile = session.get('profile', instaloader.Profile.from_username(getContext(), PROFILE))
    posts = session.get('posts',profile.get_posts())
    posts_sorted_by_likes = sorted(posts,
                               key=lambda p: p.likes + p.comments,
                               reverse=True)
    if (len(posts_sorted_by_likes)>10):
      posts_sorted_by_likes = posts_sorted_by_likes[:10]
    
    path = pathlib.Path(__file__).parent.resolve()/'static'

    # Check whether the specified path exists or not
    isExist = os.path.exists(path)
    if not isExist:
      # Create a new directory because it does not exist 
      os.makedirs(path)
      print("The new directory is created!")

    driver = Chrome(ChromeDriverManager().install())
    driver.maximize_window()
    for post in posts_sorted_by_likes:
      driver.get(post.url)
      filename = uuid4().__str__() + '.png'
      directory = './social-bootleg/static/'
      with open(directory + filename, 'wb') as file:
        l = driver.find_element_by_tag_name('img')
        file.write(l.screenshot_as_png)
        absolutePath = pathlib.Path(__file__).parent.parent.resolve()/'img'/filename
        print(absolutePath, flush=True)
        absolutePath = 'http://localhost:5000/static/' + filename
      most_liked.append({"picture_url": f'{absolutePath}', "likes" : f'{post.likes}', "comments" : f'{post.comments}'})
    driver.quit()

    return jsonify(most_liked);

@app.route("/ghostfollowers", methods=['POST'])
def get_ghost_followers():
    user = process_json_from_enduser(request, 'username')
    profile = session.get('profile',instaloader.Profile.from_username(getContext(), user))
    likes = set()
    posts = session.get('posts',profile.get_posts())
    for post in posts:
        likes = likes | set(post.get_likes())
        time.sleep(0.2)

    followers = set(profile.get_followers())
    ghost_profiles = list(followers - likes)
    ghosts = []
    
    for ghost in ghost_profiles:
      ghosts.append({"user" : f'{ghost.full_name}', "username" : f'{ghost.username}'})
    
    return jsonify(ghosts)

@app.route("/nofollowback", methods=['POST'])
def notFollowingBack():
  username = process_json_from_enduser(request, 'username')
  context = getContext()
  profile = session.get('profile',instaloader.Profile.from_username(context, username))
  
  followers = set(profile.get_followers())
  followees = set(profile.get_followees())
  profiles_not_following_back = list(followees - followers)
  not_following_back = []

  for ghost in profiles_not_following_back:
      not_following_back.append({"user" : f'{ghost.full_name}', "username" : f'{ghost.username}'})

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

@app.route("/posts_stats", methods=['POST'])
@cross_origin()
def get_posts_stats():
  username = process_json_from_enduser(request, 'username')
  profile = session.get('profile',instaloader.Profile.from_username(getContext(), username))
  time.sleep(0.2)
  all_posts = session.get('posts',profile.get_posts())
  posts = []
  time.sleep(0.5)
  for post in all_posts:
    posts.append({'likes' : f'{post.likes}', 'comments' : f'{post.comments}', 'date' : f'{post.date}'})
  
  return jsonify(posts)

@app.route("/unanswered_comments", methods=['POST'])
def get_unaswered_comments():
  username = process_json_from_enduser(request, 'username')
  profile = session.get('profile',instaloader.Profile.from_username(getContext(), username))
  time.sleep(0.2)
  posts = session.get('posts',profile.get_posts())
  time.sleep(0.5)
  unanswered_comments = []
  unanswered = []
  for post in posts:
    comments = post.get_comments()
    time.sleep(0.2)
    temp_answers = []
    for c in comments:
      ans = c.answers
      for a in ans:
        temp_answers.append(a)
      if(len(temp_answers)==0):
        unanswered_comments.append(c)

  for c in unanswered_comments:
    unanswered.append({'author' : f'{c.owner.username}', 'text' : f'{c.text}', 'date' : f'{c.created_at_utc}'})
  return jsonify(unanswered)

@app.route("/top_fans", methods = ['POST'])
def get_top_fans():
  username = process_json_from_enduser(request, 'username')
  profile = session.get('profile',instaloader.Profile.from_username(getContext(), username))
  time.sleep(0.2)
  posts = session.get('posts',profile.get_posts())
  time.sleep(0.5)
  top_fans = {}
  for post in posts:
    comments = post.get_comments()
    time.sleep(0.2)
    temp_answers = []
    for c in comments:
      author = c.owner.username
      if author in top_fans:
        top_fans[author] += 1
      else:
        top_fans[author] = 1
  top_fans = sorted(top_fans.items(),key=operator.itemgetter(1),reverse=True)

  return jsonify(top_fans)
