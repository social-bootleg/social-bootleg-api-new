from contextlib import nullcontext
import instaloader
import json

from instaloader.instaloadercontext import InstaloaderContext


# method that provides logging in to Instagram - cookie file is loaded from file,
# if file doesn't exist, login is performed and then cookie file is saved

def getContext():
    L = instaloader.Instaloader()
    configFile = open('./loginConfiguration.json')
    config = json.load(configFile)
    
    try:
        L.load_session_from_file(config['username'])
    except FileNotFoundError:
        L.login(config['username'], config['password'])
        L.save_session_to_file()
    
    return L.context