from os import linesep
from flask import Flask, jsonify, request
import instagramy
from instaloader.structures import TopSearchResults
from instascrape import *
from selenium.webdriver import Chrome
import instaloader
import json
from instaloader.exceptions import PrivateProfileNotFollowedException, ProfileNotExistsException

app = Flask(__name__)
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
      related_tags.extend(results.get_hashtags())
  tag_names = []
  for tag in related_tags:
   tag_names.append(tag.name)
  
  return jsonify(tag_names)
  

@app.route("/engagement", methods=['POST'])
def get_engagement():
  username = process_username_json(request)
  profile = Profile(username)
  profile.scrape(headers=headers)
  followers_count = profile.followers
  posts = profile.get_recent_posts()
  # scraped, unscraped = scrape_posts(posts, silent=False, headers=headers, pause=7)
  
  likes = 0
  comments = 0
  for post in posts:
    likes = likes + post.likes
    comments = comments + post.comments
  
  engagement = (likes+comments)/followers_count
  engagement_rate = {
    "posts" : f'{likes}',
    "comments" : f'{comments}',
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

@app.route("/mostlikedposts", methods=['POST'])
def get_most_liked_posts():
    PROFILE = process_username_json(request)
    most_liked = []
    profile = instaloader.Profile.from_username(getContext(), PROFILE)
    posts_sorted_by_likes = sorted(profile.get_posts(),
                               key=lambda p: p.likes + p.comments,
                               reverse=True)
    if (len(posts_sorted_by_likes)>10):
      posts_sorted_by_likes = posts_sorted_by_likes[:10]
    
    for post in posts_sorted_by_likes:
      most_liked.append({"picture_url": f'{post.url}', "likes" : f'{post.likes}', "comments" : f'{post.comments}'})
    return jsonify(most_liked);

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
    return username, 404
  except PrivateProfileNotFollowedException:
    return "You cannot trace private profiles", 401
  followers = set(profile.get_followers())
  followees = set(profile.get_followees())
  not_following_back = list(followers - followees)

  return jsonify(not_following_back)

@app.route("/test")
def test():
  driver = Chrome()
  driver.get("https://www.instagram.com/")
  time.sleep(1)
  notnow = driver.find_element_by_xpath("//button[contains(text(), 'Akceptuję wszystko')]").click()
  #login
  time.sleep(5)
  username=driver.find_element_by_css_selector("input[name='username']")
  password=driver.find_element_by_css_selector("input[name='password']")
  username.clear()
  password.clear()
  username.send_keys("jiraikeidreams")
  password.send_keys("bibi98")
  time.sleep(2)
  login = driver.find_element_by_css_selector("button[type='submit']").click()
  time.sleep(4)
  notnow = driver.find_element_by_xpath("//button[contains(text(), 'Nie teraz')]").click()
  #searchbox
  time.sleep(2)
  searchbox=driver.find_element_by_css_selector("input[placeholder='Szukaj']")
  searchbox.clear()
  searchbox.send_keys("#cat")
  names = []
  tags = []
  links = []
  # h_name = driver.find_elements_by_xpath("//div[contains(text(), '#')]")
  hashtag = driver.find_element_by_class_name("fuqBx ").find_elements_by_tag_name("div")
  # for h in hashtag:
  #   tags.extend(h.find_elements_by_tag_name("div"))
  for t in hashtag:
    links.append(t.find_element_by_tag_name("a"))
    #links.extend(t.find_elements_by_class_name("-qQT3"))
  for l in links:
    names.append(l.get_attribute("href"))


  # for h in hashtag:
  #   p = h.get_attribute('href')
  #   if '/explore/tags' in h:
  #     names.append(h.getText())
  return jsonify(names)